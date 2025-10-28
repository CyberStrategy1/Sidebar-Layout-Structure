import os

NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
EPSS_API_URL = "https://api.first.org/data/v1/epss"
CISA_KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
NVD_API_KEY = os.getenv("NVD_API_KEY")
MODEL_PATH = "./inference_engine/models/lightgbm_model.joblib"
MODEL_VERSION = "0.1.0"
SBERT_MODEL_NAME = "all-MiniLM-L6-v2"
NER_MODEL_PATH = "en_core_web_sm"
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
model_dir = os.path.dirname(MODEL_PATH)
if not os.path.exists(model_dir):
    os.makedirs(model_dir)