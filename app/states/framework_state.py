import reflex as rx
from typing import Optional, Any
import httpx
import logging
import os
import asyncio
from datetime import datetime, timedelta, timezone
from app.utils import supabase_client
import random


class FrameworkState(rx.State):
    """Manages fetching data from multiple vulnerability intelligence frameworks."""

    is_fetching: bool = False
    fetch_error: str = ""
    kev_catalog: dict[str, dict] = {}
    kev_last_updated: Optional[datetime] = None
    framework_cache: dict[str, dict] = {}
    rate_limit_cooldown: dict[str, datetime] = {}
    framework_health: dict[str, dict] = {}

    def _check_rate_limit(self, api_name: str) -> bool:
        """Check if an API is currently in a cooldown period."""
        if api_name in self.rate_limit_cooldown:
            if datetime.now(timezone.utc) < self.rate_limit_cooldown[api_name]:
                return True
        return False

    def _set_rate_limit(self, api_name: str, duration_seconds: int):
        """Set a cooldown period for an API."""
        self.rate_limit_cooldown[api_name] = datetime.now(timezone.utc) + timedelta(
            seconds=duration_seconds
        )

    def _get_cached(self, cache_key: str, max_age_hours: int) -> Optional[dict]:
        """Retrieve data from the in-memory cache if it's not stale."""
        if cache_key in self.framework_cache:
            cached_item = self.framework_cache[cache_key]
            cached_time = cached_item.get("timestamp")
            if cached_time and datetime.now(timezone.utc) - cached_time < timedelta(
                hours=max_age_hours
            ):
                return cached_item.get("data")
        return None

    def _set_cached(self, cache_key: str, data: dict):
        """Store data in the in-memory cache with a timestamp."""
        self.framework_cache[cache_key] = {
            "data": data,
            "timestamp": datetime.now(timezone.utc),
        }

    def _normalize_score(
        self, score: float, source_range: tuple, target_range: tuple
    ) -> float:
        """Normalize a score from a source range to a target range."""
        s_min, s_max = source_range
        t_min, t_max = target_range
        if s_max - s_min == 0:
            return t_min
        return t_min + (score - s_min) * (t_max - t_min) / (s_max - s_min)

    def _calculate_cohen_kappa(self, scores: list[dict]) -> float:
        """A mock calculation for inter-rater agreement among frameworks."""
        if len(scores) < 2:
            return 1.0
        numeric_scores = [
            s["normalized_score"] for s in scores if s.get("normalized_score")
        ]
        if not numeric_scores or len(numeric_scores) < 2:
            return 0.0
        variance = sum(
            (
                (x - sum(numeric_scores) / len(numeric_scores)) ** 2
                for x in numeric_scores
            )
        ) / len(numeric_scores)
        agreement = 1 - variance / 2500
        return max(0.0, min(1.0, agreement))

    def _identify_conflicts(self, scores: dict, threshold: float = 30.0) -> list[str]:
        """Identify significant conflicts between framework scores."""
        conflicts = []
        cvss = scores.get("cvss_score", 0.0) or 0.0
        epss = scores.get("epss_score", 0.0) or 0.0
        if cvss >= 7.0 and epss < 0.02:
            conflicts.append("High CVSS, Low EPSS")
        if cvss < 5.0 and epss > 0.5:
            conflicts.append("Low CVSS, High EPSS")
        if scores.get("is_kev") and cvss < 7.0:
            conflicts.append("KEV with non-High CVSS")
        return conflicts

    def _calculate_confidence(self, scores: dict, agreement: float) -> float:
        """Calculate a confidence score based on data availability and agreement."""
        num_frameworks = len([s for s in scores if scores[s] is not None])
        base_confidence = self._normalize_score(num_frameworks, (1, 11), (0.5, 1.0))
        return min(1.0, base_confidence * (0.8 + agreement * 0.2))

    def _mock_vpr_score(self, cve_id: str) -> float:
        """Mock Tenable VPR score."""
        return round(random.uniform(0, 10), 1)

    def _mock_pxs_score(self, cve_id: str) -> float:
        """Mock Picus PXS score."""
        return round(random.uniform(0, 10), 1)

    @rx.event(background=True)
    async def fetch_cvss_data(self, cve_id: str):
        """Fetch CVSS data from the NVD API for a given CVE ID."""
        cache_key = f"cvss_{cve_id}"
        async with self:
            cached_data = self._get_cached(cache_key, 24)
        if cached_data:
            return cached_data
        async with self:
            if self._check_rate_limit("nvd"):
                logging.warning(
                    f"NVD API rate limit active. Skipping fetch for {cve_id}."
                )
                return
        nvd_api_key = os.getenv("NVD_API_KEY")
        headers = {"apiKey": nvd_api_key} if nvd_api_key else {}
        url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?cveId={cve_id}"
        async with httpx.AsyncClient() as client:
            try:
                for attempt in range(3):
                    response = await client.get(url, headers=headers, timeout=15.0)
                    if response.status_code in [429, 403]:
                        wait_time = 35 * (attempt + 1)
                        async with self:
                            self._set_rate_limit("nvd", wait_time)
                        logging.warning(
                            f"NVD rate limit hit. Retrying in {wait_time}s..."
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    response.raise_for_status()
                    data = response.json()
                    vulns = data.get("vulnerabilities", [])
                    if not vulns:
                        return
                    cve_data = vulns[0].get("cve", {})
                    metrics = cve_data.get("metrics", {})
                    cvss_v31 = metrics.get("cvssMetricV31", [{}])[0].get("cvssData", {})
                    result = {
                        "cvss_score": cvss_v31.get("baseScore"),
                        "severity": cvss_v31.get("baseSeverity"),
                        "vector": cvss_v31.get("vectorString"),
                        "version": "3.1",
                    }
                    async with self:
                        self._set_cached(cache_key, result)
                    return result
            except httpx.HTTPStatusError as e:
                logging.exception(f"Error fetching CVSS for {cve_id}: {e}")
                await supabase_client.log_api_health(
                    {
                        "api_name": "NVD",
                        "endpoint": url,
                        "status": "failure",
                        "status_code": e.response.status_code,
                        "error_message": str(e),
                    }
                )
            except Exception as e:
                logging.exception(f"Unexpected error fetching CVSS for {cve_id}: {e}")

    @rx.event(background=True)
    async def fetch_epss_data(self, cve_id: str):
        """Fetch EPSS data from the FIRST API."""
        cache_key = f"epss_{cve_id}"
        async with self:
            cached_data = self._get_cached(cache_key, 24)
        if cached_data:
            return cached_data
        url = f"https://api.first.org/data/v1/epss?cve={cve_id}"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)
                response.raise_for_status()
                data = response.json().get("data", [])
                if not data:
                    return
                epss_data = data[0]
                result = {
                    "epss_score": float(epss_data.get("epss", 0.0)),
                    "percentile": float(epss_data.get("percentile", 0.0)),
                }
                async with self:
                    self._set_cached(cache_key, result)
                return result
        except httpx.HTTPStatusError as e:
            logging.exception(f"Error fetching EPSS for {cve_id}: {e}")
        except Exception as e:
            logging.exception(f"Unexpected error fetching EPSS for {cve_id}: {e}")

    @rx.event(background=True)
    async def fetch_kev_catalog(self):
        """Download and cache the CISA KEV catalog."""
        async with self:
            if self.kev_last_updated and datetime.now(
                timezone.utc
            ) - self.kev_last_updated < timedelta(hours=24):
                return
        url = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=30.0)
                response.raise_for_status()
                data = response.json()
                catalog = {}
                for item in data.get("vulnerabilities", []):
                    catalog[item["cveID"]] = {
                        "date_added": item.get("dateAdded"),
                        "due_date": item.get("dueDate"),
                        "required_action": item.get("requiredAction"),
                        "vuln_name": item.get("vulnerabilityName"),
                    }
            async with self:
                self.kev_catalog = catalog
                self.kev_last_updated = datetime.now(timezone.utc)
                logging.info("KEV catalog updated successfully.")
        except Exception as e:
            logging.exception(f"Failed to fetch KEV catalog: {e}")

    @rx.event
    def check_kev_status(self, cve_id: str) -> dict:
        """Check if a CVE is in the local KEV catalog."""
        if cve_id in self.kev_catalog:
            kev_data = self.kev_catalog[cve_id]
            return {
                "is_kev": True,
                "date_added": kev_data.get("date_added"),
                "due_date": kev_data.get("due_date"),
                "action": kev_data.get("required_action"),
                "name": kev_data.get("vuln_name"),
            }
        return {"is_kev": False}

    @rx.event
    def calculate_ssvc_decision(self, cve_data: dict, context: dict) -> dict:
        """Calculates the SSVC decision based on a simplified decision tree."""
        is_exploited = cve_data.get("is_kev", False)
        technical_impact = context.get("technical_impact", "low")
        mission_impact = context.get("mission_impact", "low")
        if is_exploited:
            if mission_impact == "critical":
                return {
                    "decision": "Act",
                    "rationale": "Exploited with critical mission impact.",
                }
            return {
                "decision": "Attend",
                "rationale": "Exploited, but mission impact is not critical.",
            }
        if technical_impact == "total" and mission_impact in ["high", "critical"]:
            return {
                "decision": "Track*",
                "rationale": "High impact, not exploited. Monitor closely.",
            }
        return {
            "decision": "Track",
            "rationale": "Low impact and not exploited. Standard monitoring.",
        }

    @rx.event
    async def calculate_lev_score(self, cve_id: str) -> Optional[float]:
        """Calculate the Likely Exploited Vulnerability (LEV) score from EPSS data."""
        epss_data = await self.fetch_epss_data(cve_id)
        if not epss_data or not epss_data.get("epss_score"):
            return None
        current_epss = epss_data["epss_score"]
        lev_score = min(1.0, current_epss * 1.25)
        return round(lev_score, 4)

    @rx.event(background=True)
    async def fetch_microsoft_exploitability(self, cve_id: str):
        """Fetch Microsoft Exploitability Index for a given CVE."""
        cache_key = f"ms_ei_{cve_id}"
        async with self:
            cached_data = self._get_cached(cache_key, 24 * 30)
        if cached_data:
            return cached_data
        mock_db = {
            "CVE-2024-0002": {"index": 0, "category": "Exploitation Detected"},
            "CVE-2024-21412": {"index": 1, "category": "Exploitation More Likely"},
            "CVE-2024-30040": {"index": 2, "category": "Exploitation Less Likely"},
        }
        await asyncio.sleep(0.1)
        result = mock_db.get(cve_id, {"index": 3, "category": "Exploitation Unlikely"})
        async with self:
            self._set_cached(cache_key, result)
        return result

    @rx.event
    def parse_vex_document(self, vex_data: dict) -> dict:
        """Parses a VEX document (CycloneDX or CSAF) to determine exploitability status."""
        if vex_data.get("bomFormat") == "CycloneDX":
            vulns = vex_data.get("vulnerabilities", [])
            if vulns:
                analysis = vulns[0].get("analysis", {})
                return {
                    "vex_status": analysis.get("state", "under_investigation"),
                    "vex_justification": analysis.get("justification"),
                    "vex_detail": analysis.get("detail"),
                }
        return {"vex_status": "unknown"}

    @rx.event
    def calculate_rvss_score(self, cve_data: dict, robot_context: dict) -> float:
        """Calculate a mock RVSS score."""
        cvss_score = cve_data.get("cvss_score", 0.0) or 0.0
        safety_impact = {"low": 1.1, "medium": 1.3, "high": 1.6, "critical": 2.0}.get(
            robot_context.get("safety_impact", "low"), 1.0
        )
        rvss_score = min(10.0, cvss_score * safety_impact)
        return round(rvss_score, 1)

    @rx.event
    def calculate_ml_exploitability(self, cve_id: str, cve_data: dict) -> float:
        """Mock ML-based exploitability index."""
        epss_score = cve_data.get("epss_score", 0.0) or 0.0
        cvss_score = cve_data.get("cvss_score", 0.0) or 0.0
        ml_score = (
            epss_score * 0.6 + self._normalize_score(cvss_score, (0, 10), (0, 1)) * 0.4
        )
        return round(ml_score, 4)

    @rx.event(background=True)
    async def fetch_all_frameworks_enhanced(self, cve_id: str):
        """Orchestrate fetching all framework data for a CVE, with conflict resolution."""
        async with self:
            self.is_fetching = True
            self.fetch_error = ""
        try:
            tasks = {
                "cvss": self.fetch_cvss_data(cve_id),
                "epss": self.fetch_epss_data(cve_id),
                "ms_ei": self.fetch_microsoft_exploitability(cve_id),
            }
            results = await asyncio.gather(*tasks.values(), return_exceptions=True)
            framework_scores = dict(zip(tasks.keys(), results))
            final_scores = {"cve_id": cve_id}
            for key, value in framework_scores.items():
                if isinstance(value, dict):
                    final_scores.update(value)
            final_scores.update(self.check_kev_status(cve_id))
            ssvc_decision = self.calculate_ssvc_decision(
                final_scores, {"mission_impact": "high"}
            )
            final_scores.update(ssvc_decision)
            lev_score_result = await self.calculate_lev_score(cve_id)
            if lev_score_result is not None:
                final_scores["lev_score"] = lev_score_result
            final_scores["ml_exploitability"] = self.calculate_ml_exploitability(
                cve_id, final_scores
            )
            final_scores["rvss_score"] = self.calculate_rvss_score(
                final_scores, {"safety_impact": "medium"}
            )
            final_scores["vpr_score"] = self._mock_vpr_score(cve_id)
            final_scores["pxs_score"] = self._mock_pxs_score(cve_id)
            normalized_scores = [
                {
                    "name": "cvss",
                    "normalized_score": self._normalize_score(
                        final_scores.get("cvss_score", 0) or 0, (0, 10), (0, 100)
                    ),
                },
                {
                    "name": "epss",
                    "normalized_score": (final_scores.get("epss_score", 0) or 0) * 100,
                },
                {
                    "name": "vpr",
                    "normalized_score": self._normalize_score(
                        final_scores.get("vpr_score", 0) or 0, (0, 10), (0, 100)
                    ),
                },
            ]
            agreement = self._calculate_cohen_kappa(normalized_scores)
            conflicts = self._identify_conflicts(final_scores)
            confidence = self._calculate_confidence(final_scores, agreement)
            final_scores["framework_agreement"] = agreement
            final_scores["conflict_flags"] = conflicts
            final_scores["scoring_confidence"] = confidence
            async with self:
                from app.state import AppState

                app_state = await self.get_state(AppState)
                if app_state.active_organization_id:
                    db_record = {
                        "cve_id": cve_id,
                        "organization_id": app_state.active_organization_id,
                        "cvss_v3_score": final_scores.get("cvss_score"),
                        "epss_score": final_scores.get("epss_score"),
                        "is_kev": final_scores.get("is_kev", False),
                        "ssvc_decision": final_scores.get("decision"),
                        "microsoft_ei": final_scores.get("index"),
                        "vpr_score": final_scores.get("vpr_score"),
                        "pxs_score": final_scores.get("pxs_score"),
                        "framework_agreement": agreement,
                        "conflict_flags": conflicts,
                        "scoring_confidence": confidence,
                        "last_updated": datetime.now(timezone.utc).isoformat(),
                    }
                    await supabase_client.upsert_vulnerabilities([db_record])
                yield rx.toast.success(f"Full analysis for {cve_id} complete.")
        except Exception as e:
            logging.exception(f"Enhanced framework fetch failed for {cve_id}: {e}")
            async with self:
                self.fetch_error = f"An error occurred: {e}"
            yield rx.toast.error("Full analysis failed.")
        finally:
            async with self:
                self.is_fetching = False

    @rx.event(background=True)
    async def fetch_all_frameworks(self, cve_id: str):
        """Orchestrate fetching all framework data for a CVE concurrently."""
        async with self:
            self.is_fetching = True
            self.fetch_error = ""
        try:
            tasks = {
                "cvss": self.fetch_cvss_data(cve_id),
                "epss": self.fetch_epss_data(cve_id),
                "lev": self.calculate_lev_score(cve_id),
            }
            results = await asyncio.gather(*tasks.values(), return_exceptions=True)
            framework_data = dict(zip(tasks.keys(), results))
            final_scores = {"cve_id": cve_id}
            for key, value in framework_data.items():
                if isinstance(value, dict):
                    final_scores.update(value)
                elif isinstance(value, float):
                    final_scores[f"{key}_score"] = value
            kev_status = self.check_kev_status(cve_id)
            final_scores.update(kev_status)
            ssvc_decision = self.calculate_ssvc_decision(
                final_scores, {"mission_impact": "high", "technical_impact": "total"}
            )
            final_scores.update(ssvc_decision)
            ms_exploit_data = await self.fetch_microsoft_exploitability(cve_id)
            if isinstance(ms_exploit_data, dict):
                final_scores["microsoft_ei"] = ms_exploit_data.get("index")
                final_scores["microsoft_ei_category"] = ms_exploit_data.get("category")
            async with self:
                from app.state import AppState

                app_state = await self.get_state(AppState)
                if app_state.active_organization_id:
                    db_record = {
                        "cve_id": cve_id,
                        "organization_id": app_state.active_organization_id,
                        "cvss_v3_score": final_scores.get("cvss_score"),
                        "cvss_v3_vector": final_scores.get("vector"),
                        "epss_score": final_scores.get("epss_score"),
                        "epss_percentile": final_scores.get("percentile"),
                        "is_kev": final_scores.get("is_kev", False),
                        "kev_date_added": final_scores.get("date_added"),
                        "kev_due_date": final_scores.get("due_date"),
                        "ssvc_decision": final_scores.get("decision"),
                        "ssvc_rationale": {"path": final_scores.get("rationale")},
                        "microsoft_ei": final_scores.get("microsoft_ei"),
                        "microsoft_ei_category": final_scores.get(
                            "microsoft_ei_category"
                        ),
                        "lev_score": final_scores.get("lev_score"),
                        "last_updated": datetime.now(timezone.utc).isoformat(),
                    }
                    await supabase_client.upsert_vulnerabilities([db_record])
                yield rx.toast.success(f"Framework data for {cve_id} updated.")
        except Exception as e:
            logging.exception(f"Failed to fetch all frameworks for {cve_id}: {e}")
            async with self:
                self.fetch_error = f"An error occurred: {e}"
            yield rx.toast.error("Framework data fetch failed.")
        finally:
            async with self:
                self.is_fetching = False