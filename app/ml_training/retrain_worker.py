import logging
from app.utils import supabase_client
from app.ml_training.train_model import (
    train_lightgbm_model,
    prepare_labels_and_features,
)
import pandas as pd
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


async def run_retraining_for_org(org_id: str):
    """Fetches feedback, combines with base data, and retrains a model for an organization."""
    logger.info(f"Starting retraining process for organization {org_id}")
    try:
        feedback_labels = await supabase_client.get_feedback_for_org(org_id)
        if not feedback_labels or len(feedback_labels) < 100:
            logger.warning(
                f"Not enough feedback labels ({len(feedback_labels)}) for org {org_id}. Skipping."
            )
            await supabase_client.update_retraining_status(org_id, "idle")
            return
        cve_ids = [label["finding"]["cve_id"] for label in feedback_labels]
        cve_data = await supabase_client.get_cve_details_batch(cve_ids)
        with open("training_data.json", "r") as f:
            base_cves = json.load(f)
        all_cves_for_training = base_cves + cve_data
        feedback_map = {
            item["finding"]["cve_id"]: 1 if item["label"] == "exploitable" else 0
            for item in feedback_labels
        }
        logger.info("Loading SBERT model for retraining...")
        sbert_model = SentenceTransformer("all-MiniLM-L6-v2")
        X, y = await prepare_labels_and_features(all_cves_for_training, sbert_model)
        for index, row in X.iterrows():
            cve_id = row["cve_id"]
            if cve_id in feedback_map:
                y.at[index] = feedback_map[cve_id]
        X = X.drop(columns=["cve_id"])
        X = X.apply(pd.to_numeric, errors="coerce").fillna(0)
        logger.info(f"Retraining model for org {org_id} with {len(X)} samples.")
        _, metrics = train_lightgbm_model(X, y)
        precision_at_50 = metrics.get("precision_at_50", 0.0)
        logger.info(
            f"New model for org {org_id} trained. Precision@50: {precision_at_50}"
        )
        await supabase_client.update_retraining_status(
            org_id, "completed", precision=precision_at_50
        )
    except Exception as e:
        logger.exception(f"An error occurred during retraining for org {org_id}: {e}")
        await supabase_client.update_retraining_status(org_id, "failed")
        raise