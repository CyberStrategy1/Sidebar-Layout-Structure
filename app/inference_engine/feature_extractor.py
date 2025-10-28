import spacy
from sentence_transformers import SentenceTransformer
from rake_nltk import Rake
import nltk
from app.inference_engine import config, utils
import os
import logging

logger = utils.setup_logger(__name__)
try:
    nltk.data.find("corpora/stopwords")
    nltk.data.find("tokenizers/punkt")
except nltk.downloader.DownloadError as e:
    logging.exception(f"NLTK download error: {e}")
    logger.info("Downloading NLTK data (stopwords, punkt)...")
    nltk.download("stopwords", quiet=True)
    nltk.download("punkt", quiet=True)
    logger.info("NLTK data downloaded.")
try:
    sbert_model = SentenceTransformer(config.SBERT_MODEL_NAME)
    ner_model = spacy.load(config.NER_MODEL_PATH)
except Exception as e:
    logger.exception(
        f"Failed to load ML models: {e}. Feature extraction will be limited."
    )
    sbert_model = None
    ner_model = None
rake_nltk_var = Rake()


def extract_entities(text: str) -> dict:
    """Extract product and vendor entities using spaCy NER."""
    if not ner_model:
        logger.warning("NER model not loaded. Skipping entity extraction.")
        return {"products": [], "vendors": []}
    doc = ner_model(text)
    entities = {"products": [], "vendors": []}
    for ent in doc.ents:
        if ent.label_ in ["PRODUCT", "ORG"]:
            if ent.label_ == "PRODUCT":
                entities["products"].append(ent.text)
            else:
                entities["vendors"].append(ent.text)
    return entities


def get_semantic_embedding(text: str) -> list[float]:
    """Generate a semantic vector embedding using SBERT."""
    if not sbert_model:
        logger.warning("SBERT model not loaded. Skipping embedding generation.")
        return []
    embedding = sbert_model.encode(text)
    return embedding.tolist()


def extract_keywords(text: str) -> list[str]:
    """Extract technical keywords using RAKE."""
    rake_nltk_var.extract_keywords_from_text(text)
    return rake_nltk_var.get_ranked_phrases()[:10]


def analyze_references(references: list[dict]) -> dict:
    """Analyze reference URLs to detect PoC and classify sources."""
    poc_found = False
    vendor_advisories = 0
    for ref in references:
        url = ref.get("url", "").lower()
        if any(
            (
                keyword in url
                for keyword in ["exploit-db", "packetstormsecurity", "github.com/poc"]
            )
        ):
            poc_found = True
        if "vendor-advisory" in ref.get("tags", []):
            vendor_advisories += 1
    return {"poc_found": poc_found, "vendor_advisory_count": vendor_advisories}


def infer_cpe_from_description(description: str, entities: dict) -> list[str]:
    """Placeholder for inferring CPEs from description and NER entities."""
    cpes = []
    if any(
        (
            "apache http server" in product.lower()
            for product in entities.get("products", [])
        )
    ):
        cpes.append("cpe:2.3:a:apache:http_server:2.4.49:*:*:*:*:*:*:*")
    if any(
        (
            "windows server" in product.lower()
            for product in entities.get("products", [])
        )
    ):
        cpes.append("cpe:2.3:o:microsoft:windows_server_2019:-:*:*:*:*:*:*:*")
    return cpes


from app.inference_engine.cpe_dictionary import cpe_matcher
import re


def run_feature_extraction(description: str, references: list[dict]) -> dict:
    """Run all feature extraction steps on the raw data."""
    logger.info("Starting feature extraction...")
    extracted_entities = extract_entities(description)
    extracted_products_dict = {}
    for product in extracted_entities.get("products", []):
        version_match = re.search(
            f"{re.escape(product)}\\s+(?:version\\s+)?(\\d+\\.\\d+(?:\\.\\d+)?)",
            description,
            re.IGNORECASE,
        )
        version = version_match.group(1) if version_match else None
        extracted_products_dict[product] = version
    inferred_cpes = cpe_matcher.infer_cpe_from_description(
        description, extracted_products_dict
    )
    features = {
        "extracted_entities": extracted_entities,
        "inferred_cpes": inferred_cpes,
        "semantic_embedding": get_semantic_embedding(description),
        "technical_keywords": extract_keywords(description),
        "reference_analysis": analyze_references(references),
    }
    logger.info(f"Feature extraction complete. Inferred {len(inferred_cpes)} CPEs.")
    return features