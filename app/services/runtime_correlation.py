import asyncio
import logging
from typing import Any, Union
from app.integrations.siem.splunk import SplunkIntegration
from app.integrations.rmm.ninjaone import NinjaOneIntegration


class RuntimeCorrelationEngine:
    """Correlates static findings with runtime evidence from SIEM and RMM tools."""

    async def correlate_vulnerability(self, finding: dict, org_id: str) -> dict:
        """Main orchestration method for correlating a single vulnerability finding."""
        cve_id = finding.get("id")
        product_name = finding.get("product", "unknown")
        siem_evidence, rmm_evidence, exploit_proof = await asyncio.gather(
            self.query_siem_for_processes(product_name, org_id),
            self.query_rmm_for_components(product_name, org_id),
            self.check_exploit_proof_availability(cve_id),
        )
        runtime_risk = self.evaluate_runtime_risk(
            finding, siem_evidence, rmm_evidence, exploit_proof
        )
        return {
            "cve_id": cve_id,
            "static_risk_score": finding.get("universal_risk_score"),
            "runtime_confirmed": runtime_risk["is_active"],
            "true_risk_score": runtime_risk["true_risk_score"],
            "evidence": {
                "siem_logs": siem_evidence,
                "rmm_telemetry": rmm_evidence,
                "active_processes": runtime_risk["active_processes"],
                "affected_hosts": runtime_risk["affected_hosts"],
                "exploit_proof_id": runtime_risk.get("exploit_proof_id"),
                "validation_evidence": runtime_risk.get("validation_evidence"),
            },
            "containment_priority": runtime_risk["containment_priority"],
        }

    async def query_siem_for_processes(
        self, product_name: str, org_id: str
    ) -> list[dict[str, str]]:
        """Query the configured SIEM for logs related to the vulnerable product."""
        siem_client = SplunkIntegration("dummy_endpoint", "dummy_key")
        try:
            logs = await siem_client.query_logs(
                f'search process="{product_name}*"', time_range={}
            )
            return logs
        except Exception as e:
            logging.exception(f"SIEM query failed for {product_name}: {e}")
            return []

    async def query_rmm_for_components(
        self, product_name: str, org_id: str
    ) -> list[dict[str, str]]:
        """Query the configured RMM for endpoints running the vulnerable component."""
        rmm_client = NinjaOneIntegration("dummy_endpoint", "dummy_key")
        try:
            installed_software = await rmm_client.get_installed_software("all_hosts")
            return [
                s
                for s in installed_software
                if product_name.lower() in s.get("name", "").lower()
            ]
        except Exception as e:
            logging.exception(f"RMM query failed for {product_name}: {e}")
            return []

    async def check_exploit_proof_availability(self, cve_id: str) -> dict | None:
        """Check if a confirmed exploit proof exists for the CVE and return it."""
        from app.utils import supabase_client

        proofs = await supabase_client.get_exploit_proofs_for_cve(
            cve_id, validation_status="confirmed"
        )
        return proofs[0] if proofs else None

    def evaluate_runtime_risk(
        self,
        finding: dict,
        siem_evidence: list,
        rmm_evidence: list,
        exploit_proof: dict | None,
    ) -> dict[str, bool | float | list[str] | str | None]:
        """Combine static and runtime evidence to determine the true risk."""
        active_processes = []
        affected_hosts = set()
        is_active = False
        if siem_evidence:
            is_active = True
            for log in siem_evidence:
                active_processes.append(log.get("process"))
                affected_hosts.add(log.get("host"))
        exploit_proof_available = bool(exploit_proof)
        runtime_multiplier = 0.3
        if is_active:
            runtime_multiplier = 1.5
            if exploit_proof_available:
                maturity = exploit_proof.get("maturity_level", "poc")
                if maturity == "weaponized":
                    runtime_multiplier = 3.0
                elif maturity == "functional":
                    runtime_multiplier = 2.5
                else:
                    runtime_multiplier = 2.0
        elif exploit_proof_available:
            runtime_multiplier = 0.8
        static_score = finding.get("universal_risk_score", 0)
        true_risk_score = static_score * runtime_multiplier
        containment_priority = "low"
        if true_risk_score > 150:
            containment_priority = "immediate"
        elif true_risk_score > 100:
            containment_priority = "high"
        result = {
            "is_active": is_active,
            "exploit_proof_available": exploit_proof_available,
            "true_risk_score": round(min(100.0, true_risk_score), 2),
            "active_processes": list(set(active_processes)),
            "affected_hosts": list(affected_hosts),
            "containment_priority": containment_priority,
        }
        if exploit_proof:
            result["exploit_proof_id"] = exploit_proof.get("id")
            result["validation_evidence"] = exploit_proof.get("validation_evidence")
        return result