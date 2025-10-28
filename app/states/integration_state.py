import reflex as rx
from typing import Literal
import logging
from app.integrations.siem.splunk import SplunkIntegration
from app.integrations.rmm.ninjaone import NinjaOneIntegration
from app.services.runtime_correlation import RuntimeCorrelationEngine
from app.states.risk_intelligence_state import RiskIntelligenceState


class IntegrationState(rx.State):
    """Manages configuration and status of SIEM/RMM integrations."""

    siem_provider: Literal["none", "splunk", "sentinel", "stellar_cyber"] = "none"
    siem_endpoint: str = ""
    siem_api_key: str = ""
    siem_connection_status: str = "not_configured"
    is_saving_siem: bool = False
    rmm_provider: Literal["none", "ninjaone", "datto", "manageengine"] = "none"
    rmm_endpoint: str = ""
    rmm_api_key: str = ""
    rmm_connection_status: str = "not_configured"
    is_saving_rmm: bool = False
    correlation_enabled: bool = False
    auto_containment_enabled: bool = False
    correlation_results: dict[str, dict] = {}
    is_correlating: bool = False

    @rx.event(background=True)
    async def test_siem_connection(self):
        """Simulates testing the SIEM connection."""
        async with self:
            self.siem_connection_status = "testing"
        import asyncio

        await asyncio.sleep(2)
        if self.siem_api_key == "valid-key":
            async with self:
                self.siem_connection_status = "success"
            yield rx.toast.success("SIEM connection successful!")
        else:
            async with self:
                self.siem_connection_status = "failure"
            yield rx.toast.error("SIEM connection failed. Check credentials.")

    @rx.event(background=True)
    async def test_rmm_connection(self):
        """Simulates testing the RMM connection."""
        async with self:
            self.rmm_connection_status = "testing"
        import asyncio

        await asyncio.sleep(2)
        if self.rmm_api_key == "valid-key":
            async with self:
                self.rmm_connection_status = "success"
            yield rx.toast.success("RMM connection successful!")
        else:
            async with self:
                self.rmm_connection_status = "failure"
            yield rx.toast.error("RMM connection failed. Check credentials.")

    @rx.event(background=True)
    async def save_siem_config(self, form_data: dict):
        """Saves SIEM configuration."""
        async with self:
            self.is_saving_siem = True
            self.siem_provider = form_data.get("siem_provider")
            self.siem_endpoint = form_data.get("siem_endpoint")
            self.siem_api_key = form_data.get("siem_api_key")
        import asyncio

        await asyncio.sleep(1)
        async with self:
            self.is_saving_siem = False
        yield rx.toast.success("SIEM configuration saved.")

    @rx.event(background=True)
    async def save_rmm_config(self, form_data: dict):
        """Saves RMM configuration."""
        async with self:
            self.is_saving_rmm = True
            self.rmm_provider = form_data.get("rmm_provider")
            self.rmm_endpoint = form_data.get("rmm_endpoint")
            self.rmm_api_key = form_data.get("rmm_api_key")
        import asyncio

        await asyncio.sleep(1)
        async with self:
            self.is_saving_rmm = False
        yield rx.toast.success("RMM configuration saved.")

    @rx.var
    def correlation_results_list(self) -> list[dict]:
        """Returns the correlation results as a list for data_table."""
        return list(self.correlation_results.values())

    @rx.event(background=True)
    async def run_correlation_for_finding(self, cve_id: str):
        """Runs the runtime correlation engine for a specific finding."""
        async with self:
            self.is_correlating = True
            risk_intel_state = await self.get_state(RiskIntelligenceState)
            finding = next(
                (f for f in risk_intel_state.all_cves if f["cve_id"] == cve_id), None
            )
        if not finding:
            yield rx.toast.error(f"Finding {cve_id} not found.")
            async with self:
                self.is_correlating = False
            return
        engine = RuntimeCorrelationEngine()
        try:
            result = await engine.correlate_vulnerability(
                finding, org_id="dummy-org-id"
            )
            async with self:
                self.correlation_results[cve_id] = result
            yield rx.toast.success(f"Runtime correlation complete for {cve_id}.")
        except Exception as e:
            logging.exception(f"Correlation failed for {cve_id}: {e}")
            yield rx.toast.error("Correlation failed.")
        finally:
            async with self:
                self.is_correlating = False