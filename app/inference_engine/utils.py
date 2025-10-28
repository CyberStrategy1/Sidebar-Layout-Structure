import logging
from app.inference_engine import config


def setup_logger(name: str):
    """Set up a logger with a standard format."""
    logging.basicConfig(level=config.LOG_LEVEL, format=config.LOG_FORMAT)
    return logging.getLogger(name)


def validate_cve_id(cve_id: str) -> bool:
    """Basic validation for CVE ID format."""
    import re

    return bool(re.match("^CVE-\\d{4}-\\d{4,}$", cve_id))


def sanitize_input(text: str) -> str:
    """Basic input sanitization."""
    return text.strip()