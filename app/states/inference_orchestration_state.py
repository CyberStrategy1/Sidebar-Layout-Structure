import reflex as rx
from typing import Optional
import logging
import asyncio
from datetime import datetime, timedelta, timezone
from app.utils import supabase_client
from app.inference_engine.main import run_inference_pipeline


class InferenceOrchestrationState(rx.State):
    """Manages the end-to-end inference pipeline for an organization."""

    is_running: bool = False
    current_org_id: str = ""
    cves_processed: int = 0
    cves_total: int = 0
    errors: list[str] = []
    last_run_timestamp: Optional[str] = None

    @rx.event(background=True)
    async def run_inference_for_organization(self, org_id: str):
        """Main orchestration function to run inference for a given organization."""
        async with self:
            if self.is_running:
                logging.warning(
                    f"Inference for org {org_id} skipped, another job is running."
                )
                yield rx.toast.warning("Inference job already in progress.")
                return
            self.is_running = True
            self.current_org_id = org_id
            self.cves_processed = 0
            self.cves_total = 0
            self.errors = []
        try:
            unenriched_cves = await supabase_client.get_unenriched_cves(org_id, days=30)
            if not unenriched_cves:
                yield rx.toast.info("No new CVEs to enrich for this organization.")
                return
            async with self:
                self.cves_total = len(unenriched_cves)
            yield rx.toast.info(
                f"Starting inference for {self.cves_total} CVEs in org {org_id}."
            )
            for cve in unenriched_cves:
                cve_id = cve.get("id")
                if not cve_id:
                    continue
                try:
                    enriched_data = await run_inference_pipeline(cve_id)
                    if enriched_data:
                        enriched_data["organization_id"] = org_id
                        enriched_data["explainability_features"] = {
                            "epss_score": {
                                "weight": 45,
                                "value": enriched_data.get("predicted_epss"),
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
                        }
                        await supabase_client.upsert_inference_finding(enriched_data)
                    async with self:
                        self.cves_processed += 1
                except Exception as e:
                    logging.exception(
                        f"Failed to process CVE {cve_id} for org {org_id}: {e}"
                    )
                    async with self:
                        self.errors.append(f"Error on {cve_id}: {str(e)}")
                    continue
            async with self:
                self.last_run_timestamp = datetime.now(timezone.utc).isoformat()
                from app.states.risk_intelligence_state import RiskIntelligenceState

                yield RiskIntelligenceState.load_all_cve_data
                yield rx.toast.success(
                    f"Inference complete for org {org_id}. Processed {self.cves_processed} CVEs."
                )
        except Exception as e:
            logging.exception(f"Inference orchestration failed for org {org_id}: {e}")
            yield rx.toast.error(f"Inference job failed for org {org_id}.")
        finally:
            async with self:
                self.is_running = False
                self.current_org_id = ""