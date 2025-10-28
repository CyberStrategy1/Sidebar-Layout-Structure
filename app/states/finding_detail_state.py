import reflex as rx
from typing import Optional, TypedDict
import logging
from app.utils import supabase_client
from app.state import AppState
from app.states.feedback_state import FeedbackState


class Finding(TypedDict):
    id: int
    cve_id: str
    organization_id: str
    raw_description: str
    raw_references: list[str]
    raw_cwe_ids: list[str]
    extracted_products: dict
    extracted_attack_vectors: dict
    technical_keywords: list[str]
    semantic_embedding: list[float]
    predicted_severity: str
    severity_confidence: float
    predicted_epss: float
    predicted_impact_score: float
    exploitation_likelihood: str
    risk_category: str
    attack_complexity: str
    requires_user_interaction: bool
    inference_timestamp: str
    model_version: str
    confidence_score: float
    processing_time_ms: int
    explainability_features: dict


class FindingDetailState(rx.State):
    """Manages the state for the finding detail side panel."""

    selected_finding: Optional[Finding] = None
    is_panel_open: bool = False
    show_explainability_modal: bool = False
    is_loading: bool = False

    def _format_feature_name(self, key: str) -> str:
        """Convert feature keys to human-readable names."""
        mapping = {
            "epss_score": "EPSS Score",
            "public_ip": "Public IP Exposure",
            "poc_exists": "PoC Code Exists",
            "cve_age": "CVE Age",
            "in_tech_stack": "Affects Your Stack",
            "cvss_score": "CVSS Base Score",
            "is_kev": "In CISA KEV Catalog",
            "exploit_maturity": "Exploit Maturity",
        }
        return mapping.get(key, key.replace("_", " ").title())

    @rx.var
    def top_contributing_features(self) -> list[dict]:
        """Extract top 3 features from explainability_features JSONB."""
        if not self.selected_finding:
            return []
        features = self.selected_finding.get("explainability_features", {})
        if not features:
            return []
        if not isinstance(features, dict):
            return []
        sorted_features = sorted(
            features.items(), key=lambda x: x[1].get("weight", 0), reverse=True
        )[:3]
        return [
            {
                "name": self._format_feature_name(key),
                "weight": value.get("weight", 0),
                "value": value.get("value", "True"),
                "description": value.get("description", ""),
            }
            for key, value in sorted_features
        ]

    @rx.var
    def all_explainability_features(self) -> list[dict]:
        """All features for expanded modal."""
        if not self.selected_finding:
            return []
        features = self.selected_finding.get("explainability_features", {})
        if not features:
            return []
        if not isinstance(features, dict):
            return []
        sorted_features = sorted(
            features.items(), key=lambda x: x[1].get("weight", 0), reverse=True
        )
        return [
            {
                "name": self._format_feature_name(key),
                "weight": value.get("weight", 0),
                "value": value.get("value"),
                "description": value.get("description", ""),
            }
            for key, value in sorted_features
        ]

    @rx.event(background=True)
    async def open_finding_detail(self, cve_id: str):
        """Opens the panel and loads the full finding data."""
        async with self:
            self.is_loading = True
            self.is_panel_open = True
            app_state = await self.get_state(AppState)
            org_id = app_state.active_organization_id
        if not org_id:
            async with self:
                self.is_loading = False
            return
        try:
            from app.states.risk_intelligence_state import RiskIntelligenceState

            async with self:
                risk_state = await self.get_state(RiskIntelligenceState)
                cve_data = next(
                    (cve for cve in risk_state.all_cves if cve["cve_id"] == cve_id),
                    None,
                )
            if not cve_data:
                raise ValueError(f"Finding for {cve_id} not found.")
            import hashlib

            finding_id = (
                int(hashlib.sha256(cve_id.encode("utf-8")).hexdigest(), 16) % 10**8
            )
            mock_finding = {
                **cve_data,
                "id": finding_id,
                "organization_id": org_id,
                "raw_description": cve_data.get(
                    "description", "No raw description available."
                ),
                "raw_references": ["https://nvd.nist.gov/vuln/detail/" + cve_id],
                "raw_cwe_ids": ["CWE-79"],
                "extracted_products": {"Apache": "2.4.49"},
                "extracted_attack_vectors": {"RCE": "via crafted HTTP request"},
                "technical_keywords": ["http", "rce", "buffer overflow"],
                "semantic_embedding": [0.1] * 384,
                "predicted_severity": cve_data.get("severity", "CRITICAL"),
                "severity_confidence": 0.8921,
                "predicted_epss": cve_data.get("epss_score", 0.0),
                "predicted_impact_score": cve_data.get("universal_risk_score", 0.0),
                "exploitation_likelihood": "Very High",
                "risk_category": "RCE",
                "attack_complexity": "Low",
                "requires_user_interaction": False,
                "inference_timestamp": "2024-07-30T10:00:00Z",
                "model_version": "0.1.0",
                "confidence_score": 0.8921,
                "processing_time_ms": 2451,
                "explainability_features": {
                    "epss_score": {
                        "weight": 45,
                        "value": cve_data.get("epss_score", 0.0),
                        "description": "High probability of exploitation.",
                    },
                    "public_ip": {
                        "weight": 30,
                        "value": "True",
                        "description": "Asset is exposed to the internet.",
                    },
                    "poc_exists": {
                        "weight": 25,
                        "value": "True",
                        "description": "Proof-of-concept exploit code is publicly available.",
                    },
                },
            }
            async with self:
                self.selected_finding = mock_finding
                feedback_state = await self.get_state(FeedbackState)
                await feedback_state.get_feedback_for_finding(finding_id)
        except Exception as e:
            logging.exception(f"Error opening finding detail: {e}")
            async with self:
                yield rx.toast.error(f"Could not load finding {cve_id}")
                self.is_panel_open = False
        finally:
            async with self:
                self.is_loading = False

    @rx.event
    def close_finding_detail(self):
        """Closes the side panel."""
        self.is_panel_open = False
        self.selected_finding = None

    @rx.event
    def toggle_explainability_modal(self):
        """Toggles the explainability modal."""
        self.show_explainability_modal = not self.show_explainability_modal