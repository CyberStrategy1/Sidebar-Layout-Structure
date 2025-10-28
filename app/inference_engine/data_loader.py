import httpx
import asyncio
from app.inference_engine import config, utils

logger = utils.setup_logger(__name__)


async def fetch_nvd_data(cve_id: str) -> dict:
    """Fetch raw CVE data from the NVD API."""
    if not config.NVD_API_KEY:
        logger.warning("NVD_API_KEY not set. NVD fetch will be limited.")
    headers = {"apiKey": config.NVD_API_KEY} if config.NVD_API_KEY else {}
    url = f"{config.NVD_API_URL}?cveId={cve_id}"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            vulns = data.get("vulnerabilities", [])
            if vulns:
                logger.info(f"Successfully fetched NVD data for {cve_id}")
                return vulns[0].get("cve", {})
            return {}
    except httpx.HTTPError as e:
        logger.exception(f"HTTP error fetching NVD data for {cve_id}: {e}")
        return {}


async def fetch_epss_data(cve_id: str) -> dict:
    """Fetch EPSS score from FIRST.org."""
    url = f"{config.EPSS_API_URL}?cve={cve_id}"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            data = response.json().get("data", [])
            if data:
                logger.info(f"Successfully fetched EPSS data for {cve_id}")
                return data[0]
            return {}
    except httpx.HTTPError as e:
        logger.exception(f"HTTP error fetching EPSS data for {cve_id}: {e}")
        return {}


async def fetch_kev_data() -> dict:
    """Fetch the CISA KEV catalog."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(config.CISA_KEV_URL, timeout=30.0)
            response.raise_for_status()
            logger.info("Successfully fetched CISA KEV catalog.")
            return response.json()
    except httpx.HTTPError as e:
        logger.exception(f"HTTP error fetching KEV data: {e}")
        return {}


async def get_all_data(cve_id: str) -> dict:
    """Orchestrate fetching data from all sources for a given CVE ID."""
    if not utils.validate_cve_id(cve_id):
        logger.error(f"Invalid CVE ID format: {cve_id}")
        return {}
    tasks = {
        "nvd": fetch_nvd_data(cve_id),
        "epss": fetch_epss_data(cve_id),
        "kev": fetch_kev_data(),
    }
    results = await asyncio.gather(*tasks.values(), return_exceptions=True)
    raw_data = {}
    for name, result in zip(tasks.keys(), results):
        if isinstance(result, Exception):
            logger.error(f"Error fetching data for {name}: {result}")
            raw_data[name] = {}
        else:
            raw_data[name] = result
    return raw_data