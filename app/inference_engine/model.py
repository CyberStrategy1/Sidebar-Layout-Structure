import joblib
import numpy as np
from app.inference_engine import config, utils
import logging
import pandas as pd

logger = utils.setup_logger(__name__)
try:
    model = joblib.load(config.MODEL_PATH)
    logger.info(f"Model loaded from {config.MODEL_PATH}")
except FileNotFoundError as e:
    logging.exception(
        f"CRITICAL: Model file not found at {config.MODEL_PATH}. The application cannot make predictions. Please train a model first using `python -m scripts.train_initial_model --fetch-nvd --train --evaluate`. {e}"
    )
    model = None
except Exception as e:
    logging.exception(f"CRITICAL: Error loading model from {config.MODEL_PATH}: {e}")
    model = None


def predict(features: dict) -> dict:
    """Make predictions using the loaded LightGBM model."""
    if not model:
        raise RuntimeError("Model not loaded. Cannot make predictions.")
    feature_df = pd.DataFrame([features])
    data_for_prediction = {}
    data_for_prediction["cvss_base_score"] = features.get("cvss_score", 0.0)
    data_for_prediction["epss_score"] = features.get("epss_score", 0.0)
    data_for_prediction["is_kev"] = 1 if features.get("is_kev", False) else 0
    try:
        prediction_features = pd.DataFrame([data_for_prediction])
        prediction_proba = model.predict_proba(prediction_features)[:, 1]
        prediction_class = (prediction_proba > 0.5).astype(int)
        return {
            "predicted_exploitability": float(prediction_class[0]),
            "prediction_probability": float(prediction_proba[0]),
        }
    except Exception as e:
        logger.exception(
            f"Prediction failed: {e}. Features might not match model expectations."
        )
        return {
            "predicted_exploitability": None,
            "prediction_probability": None,
            "error": str(e),
        }


def get_feature_importance() -> list[dict]:
    """Get feature importance from the loaded model."""
    if not model or not hasattr(model, "feature_importances_"):
        return []
    feature_names = (
        model.feature_name_
        if hasattr(model, "feature_name_")
        else [f"feature_{i}" for i in range(len(model.feature_importances_))]
    )
    importances = model.feature_importances_
    feature_importance_dict = dict(zip(feature_names, importances))

    def get_importance(item):
        return item[1]

    sorted_features = sorted(
        feature_importance_dict.items(), key=get_importance, reverse=True
    )
    return [
        {"feature": name, "importance": float(imp)} for name, imp in sorted_features
    ]


def calculate_confidence(prediction_probability: float) -> float:
    """Calculate a confidence score based on the model's prediction probability."""
    return round(prediction_probability, 4)