import httpx
import json
import os
import logging
from pathlib import Path
from typing import Optional
import asyncio
from datetime import datetime, timezone
import re

logger = logging.getLogger(__name__)
CPE_DICT_URL = "https://nvd.nist.gov/feeds/json/cpematch/1.0/nvdcpematch-1.0.json.gz"
CPE_CACHE_PATH = "./inference_engine/data/cpe_dictionary.json"


class CPEMatcher:
    """Fuzzy matcher for product names to CPE URIs."""

    def __init__(self):
        self.cpe_dict: dict[str, list[dict]] = {}
        self.loaded = False

    async def load_cpe_dictionary(self):
        """Load CPE dictionary from cache or download from NVD."""
        cache_path = Path(CPE_CACHE_PATH)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        if cache_path.exists():
            cache_age = (
                datetime.now(timezone.utc).timestamp() - cache_path.stat().st_mtime
            )
            if cache_age < 7 * 24 * 3600:
                logger.info("Loading CPE dictionary from cache...")
                with open(cache_path, "r") as f:
                    self.cpe_dict = json.load(f)
                    self.loaded = True
                    logger.info(f"Loaded {len(self.cpe_dict)} CPE entries from cache")
                    return
        logger.info("Downloading CPE dictionary from NVD...")
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(CPE_DICT_URL)
                response.raise_for_status()
                import gzip

                decompressed = gzip.decompress(response.content)
                data = json.loads(decompressed)
                for match in data.get("matches", []):
                    cpe23_uri = match.get("cpe23Uri", "")
                    if not cpe23_uri:
                        continue
                    parts = cpe23_uri.split(":")
                    if len(parts) >= 5:
                        vendor = parts[3].replace("_", " ").lower()
                        product = parts[4].replace("_", " ").lower()
                        version = parts[5] if len(parts) > 5 else "*"
                        if product not in self.cpe_dict:
                            self.cpe_dict[product] = []
                        self.cpe_dict[product].append(
                            {
                                "cpe_uri": cpe23_uri,
                                "vendor": vendor,
                                "product": product,
                                "version": version,
                            }
                        )
                with open(cache_path, "w") as f:
                    json.dump(self.cpe_dict, f)
                self.loaded = True
                logger.info(f"Downloaded and cached {len(self.cpe_dict)} CPE entries")
        except Exception as e:
            logger.exception(f"Failed to load CPE dictionary: {e}")
            self.cpe_dict = {}
            self.loaded = True

    def fuzzy_match_product(
        self, product_name: str, max_results: int = 5
    ) -> list[dict]:
        """
        Fuzzy match a product name to CPE URIs.
        """
        if not self.loaded:
            logger.warning(
                "CPE dictionary not loaded. Call load_cpe_dictionary() first."
            )
            return []
        product_lower = product_name.lower().replace("-", " ")
        matches = []
        if product_lower in self.cpe_dict:
            for cpe in self.cpe_dict[product_lower][:max_results]:
                matches.append({**cpe, "confidence": 1.0, "match_type": "exact"})
            return matches
        for cpe_product, cpe_list in self.cpe_dict.items():
            if product_lower in cpe_product or cpe_product in product_lower:
                for cpe in cpe_list[:2]:
                    matches.append({**cpe, "confidence": 0.8, "match_type": "partial"})
        if not matches:
            best_matches = []
            for cpe_product in self.cpe_dict.keys():
                product_words = set(product_lower.split())
                cpe_words = set(cpe_product.split())
                shared = len(product_words & cpe_words)
                if shared > 0:
                    similarity = shared / max(len(product_words), len(cpe_words))
            if similarity > 0.3:
                best_matches.append((cpe_product, similarity))

            def get_similarity(item):
                return item[1]

            best_matches.sort(key=get_similarity, reverse=True)
            for cpe_product, similarity in best_matches[:max_results]:
                for cpe in self.cpe_dict[cpe_product][:1]:
                    matches.append(
                        {
                            **cpe,
                            "confidence": round(similarity, 2),
                            "match_type": "fuzzy",
                        }
                    )
        return matches[:max_results]

    def infer_cpe_from_description(
        self, description: str, extracted_products: dict
    ) -> list[dict]:
        """
        Infer CPE URIs from CVE description and NER-extracted products.
        """
        inferred_cpes = []
        for product_name, version in extracted_products.items():
            matches = self.fuzzy_match_product(product_name)
            for match in matches:
                if version and version != "*":
                    if match["version"] == version or match["version"] == "*":
                        match["confidence"] *= 1.2
                inferred_cpes.append(
                    {
                        "cpe_uri": match["cpe_uri"],
                        "vendor": match["vendor"],
                        "product": match["product"],
                        "version": version if version else match["version"],
                        "confidence": min(match["confidence"], 1.0),
                        "source": "ner_extraction",
                        "match_type": match["match_type"],
                    }
                )
        version_pattern = (
            "(\\w+(?:\\s+\\w+)*)\\s+(?:version\\s+)?(\\d+\\.\\d+(?:\\.\\d+)?)"
        )
        for match in re.finditer(version_pattern, description, re.IGNORECASE):
            product_name = match.group(1)
            version = match.group(2)
            cpe_matches = self.fuzzy_match_product(product_name)
            for cpe_match in cpe_matches[:2]:
                inferred_cpes.append(
                    {
                        "cpe_uri": cpe_match["cpe_uri"],
                        "vendor": cpe_match["vendor"],
                        "product": product_name,
                        "version": version,
                        "confidence": cpe_match["confidence"] * 0.9,
                        "source": "regex_extraction",
                        "match_type": cpe_match["match_type"],
                    }
                )
        seen_cpes = set()
        unique_cpes = []

        def get_confidence(item):
            return item["confidence"]

        for cpe in sorted(inferred_cpes, key=get_confidence, reverse=True):
            cpe_key = f"{cpe['cpe_uri']}:{cpe['version']}"
            if cpe_key not in seen_cpes:
                seen_cpes.add(cpe_key)
                unique_cpes.append(cpe)
        return unique_cpes[:10]


cpe_matcher = CPEMatcher()