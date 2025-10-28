import asyncio
import time
import json
from app.inference_engine import data_loader, feature_extractor, model, config, utils

logger = utils.setup_logger(__name__)


async def run_inference_pipeline(cve_id: str) -> dict:
    """Orchestrate the full CVE enrichment pipeline with CPE inference."""
    start_time = time.time()
    logger.info(f"Starting inference for CVE: {cve_id}")
    raw_data = await data_loader.get_all_data(cve_id)
    if not raw_data.get("nvd"):
        logger.error(f"Failed to get base NVD data for {cve_id}. Aborting.")
        return {}
    nvd_cve_data = raw_data.get("nvd", {})
    description = nvd_cve_data.get("descriptions", [{"value": ""}])[0]["value"]
    references = nvd_cve_data.get("references", [])
    extracted_features = feature_extractor.run_feature_extraction(
        description, references
    )
    metrics = nvd_cve_data.get("metrics", {})
    cvss_metrics = metrics.get("cvssMetricV31", [{}])[0].get("cvssData", {})
    engineered_features = {
        "cvss_base_score": cvss_metrics.get("baseScore", 0.0),
        "epss_score": raw_data.get("epss", {}).get("epss", 0.0),
        "is_kev": 1
        if raw_data.get("kev") and cve_id in raw_data["kev"].get("vulnerabilities", {})
        else 0,
    }
    try:
        predictions = model.predict(engineered_features)
    except RuntimeError as e:
        logger.exception(f"Inference pipeline failed for {cve_id}: {e}")
        return {"error": str(e)}
    feature_importance = model.get_feature_importance()
    processing_time_ms = int((time.time() - start_time) * 1000)
    enriched_object = {
        "cve_id": cve_id,
        "raw_description": description,
        "raw_references": [ref.get("url") for ref in references],
        "inferred_cpes": extracted_features.get("inferred_cpes", []),
        "predicted_exploitability": predictions.get("predicted_exploitability"),
        "prediction_probability": predictions.get("prediction_probability"),
        "feature_importance": feature_importance,
        "inference_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "model_version": config.MODEL_VERSION,
        "processing_time_ms": processing_time_ms,
    }
    logger.info(
        f"Inference complete. Inferred {len(enriched_object['inferred_cpes'])} CPEs."
    )
    return enriched_object


async def main(cve_id: str):
    """Main entry point for command-line execution."""
    result = await run_inference_pipeline(cve_id)
    if result:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        cve_to_process = sys.argv[1]
        asyncio.run(main(cve_to_process))
    else:
        print("Usage: python -m app.inference_engine.main <CVE-ID>")