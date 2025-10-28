import httpx
import asyncio
import json
import os
import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score
import joblib
from datetime import datetime, timedelta
from sentence_transformers import SentenceTransformer
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
EPSS_API_URL = "https://api.first.org/data/v1/epss"
KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
MODEL_SAVE_PATH = "./inference_engine/models/lightgbm_model.joblib"
METRICS_SAVE_PATH = "./inference_engine/models/model_metrics.json"


async def fetch_nvd_data(days=365, limit=10000):
    logger.info(f"Fetching last {days} days of CVEs from NVD...")
    all_cves = []
    nvd_api_key = os.getenv("NVD_API_KEY")
    headers = {"apiKey": nvd_api_key} if nvd_api_key else {}
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    start_index = 0
    total_results = 1
    async with httpx.AsyncClient(timeout=60.0) as client:
        while start_index < total_results and len(all_cves) < limit:
            url = f"{NVD_API_URL}?pubStartDate={start_date.isoformat()}Z&pubEndDate={end_date.isoformat()}Z&resultsPerPage=2000&startIndex={start_index}"
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                vulnerabilities = data.get("vulnerabilities", [])
                all_cves.extend([v["cve"] for v in vulnerabilities])
                total_results = data.get("totalResults", 0)
                start_index += len(vulnerabilities)
                logger.info(f"Fetched {len(all_cves)}/{total_results} CVEs...")
                await asyncio.sleep(1)
            except httpx.HTTPStatusError as e:
                logging.exception(f"HTTP error fetching NVD data: {e}")
                if e.response.status_code == 403:
                    logger.error("Forbidden. Check your NVD API Key.")
                break
            except Exception as e:
                logging.exception(f"An error occurred: {e}")
                break
    return all_cves[:limit]


def engineer_features(cve_data, sbert_model):
    features = {}
    cve_id = cve_data.get("id", "N/A")
    features["cve_id"] = cve_id
    metrics = cve_data.get("metrics", {})
    cvss_v31 = metrics.get("cvssMetricV31", [{}])[0].get("cvssData", {})
    features["cvss_base_score"] = cvss_v31.get("baseScore", 0.0)
    description = cve_data.get("descriptions", [{}])[0].get("value", "")
    features["description_length"] = len(description)
    description_lower = description.lower()
    features["has_rce"] = 1 if "remote code execution" in description_lower else 0
    features["has_privilege_escalation"] = (
        1 if "privilege escalation" in description_lower else 0
    )
    features["has_authentication"] = 1 if "authentication" in description_lower else 0
    embedding = sbert_model.encode(description)
    for i, val in enumerate(embedding):
        features[f"sbert_{i}"] = val
    references = cve_data.get("references", [])
    features["reference_count"] = len(references)
    features["has_poc"] = (
        1
        if any(("exploit-db" in ref.get("url", "").lower() for ref in references))
        else 0
    )
    features["has_vendor_advisory"] = (
        1
        if any(("vendor-advisory" in ref.get("tags", []) for ref in references))
        else 0
    )
    weaknesses = cve_data.get("weaknesses", [{}])[0].get("description", [{}])
    cwe = weaknesses[0].get("value", "N/A") if weaknesses else "N/A"
    features["cwe"] = cwe
    published_date = datetime.fromisoformat(cve_data["published"])
    features["cve_age_days"] = (
        datetime.utcnow().replace(tzinfo=None) - published_date.replace(tzinfo=None)
    ).days
    return features


async def prepare_labels_and_features(cves, sbert_model):
    logger.info("Fetching EPSS and KEV data for labeling...")
    async with httpx.AsyncClient() as client:
        epss_response = await client.get(EPSS_API_URL)
        epss_data = {item["cve"]: item for item in epss_response.json()["data"]}
        kev_response = await client.get(KEV_URL)
        kev_cves = {item["cveID"] for item in kev_response.json()["vulnerabilities"]}
    all_features = []
    labels = []
    for cve in cves:
        features = engineer_features(cve, sbert_model)
        cve_id = cve["id"]
        features["epss_score"] = float(epss_data.get(cve_id, {}).get("epss", 0.0))
        features["epss_percentile"] = float(
            epss_data.get(cve_id, {}).get("percentile", 0.0)
        )
        features["is_kev"] = 1 if cve_id in kev_cves else 0
        all_features.append(features)
        exploitable = 0
        if features["is_kev"] or (
            features["epss_score"] > 0.7 and features.get("cvss_base_score", 0) > 7.0
        ):
            exploitable = 1
        labels.append(exploitable)
    df = pd.DataFrame(all_features)
    df["label"] = labels
    df = pd.get_dummies(df, columns=["cwe"], prefix="cwe")
    return (df.drop(columns=["cve_id"]), df["label"])


def calculate_precision_at_k(y_true, y_pred_proba, k_percent=50):
    k = int(len(y_true) * (k_percent / 100.0))
    top_k_indices = np.argsort(y_pred_proba)[-k:]
    true_labels_at_top_k = y_true[top_k_indices]
    precision = np.sum(true_labels_at_top_k) / k if k > 0 else 0
    return precision


def train_lightgbm_model(X, y):
    logger.info("Training LightGBM model...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    model = lgb.LGBMClassifier(
        objective="binary",
        metric="auc",
        n_estimators=1000,
        learning_rate=0.05,
        num_leaves=31,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(
        X_train,
        y_train,
        eval_set=[(X_test, y_test)],
        eval_metric="auc",
        callbacks=[lgb.early_stopping(100, verbose=False)],
    )
    logger.info("Evaluating model...")
    metrics = evaluate_model(model, X_test, y_test)
    logger.info(f"Saving model to {MODEL_SAVE_PATH}")
    joblib.dump(model, MODEL_SAVE_PATH)
    logger.info(f"Saving metrics to {METRICS_SAVE_PATH}")
    with open(METRICS_SAVE_PATH, "w") as f:
        json.dump(metrics, f, indent=4)
    return (model, metrics)


def evaluate_model(model, X_test, y_test):
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    y_pred = (y_pred_proba > 0.5).astype(int)
    precision_at_50 = calculate_precision_at_k(
        y_test.values, y_pred_proba, k_percent=50
    )
    metrics = {
        "precision": precision_score(y_test, y_pred),
        "recall": recall_score(y_test, y_pred),
        "f1_score": f1_score(y_test, y_pred),
        "auc_roc": roc_auc_score(y_test, y_pred_proba),
        "precision_at_50": precision_at_50,
    }
    logger.info(f"Model Metrics: {metrics}")
    return metrics


async def run_training_pipeline(fetch_new_data=False, data_limit=10000):
    if fetch_new_data:
        cves = await fetch_nvd_data(limit=data_limit)
        with open("training_data.json", "w") as f:
            json.dump(cves, f)
    else:
        try:
            with open("training_data.json", "r") as f:
                cves = json.load(f)
        except FileNotFoundError as e:
            logging.exception(
                f"training_data.json not found. Run with --fetch-nvd to get data. {e}"
            )
            return
    logger.info("Loading SBERT model for embeddings...")
    sbert_model = SentenceTransformer("all-MiniLM-L6-v2")
    X, y = await prepare_labels_and_features(cves, sbert_model)
    X = X.apply(pd.to_numeric, errors="coerce").fillna(0)
    train_lightgbm_model(X, y)
    logger.info("Training pipeline complete!")