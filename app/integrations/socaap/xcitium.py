import httpx
import logging
import os
from typing import Any, Union


class XcitiumSOCaaPIntegration:
    """Integration for Xcitium SOCaaP for automated containment."""

    def __init__(self):
        self.api_endpoint = os.getenv("XCITIUM_API_ENDPOINT")
        self.api_key = os.getenv("XCITIUM_API_KEY")

    async def send_containment_alert(self, evidence: dict[str, Union[str, list[str]]]):
        """Post TRUE RISK indicators to SOCaaP for containment."""
        if not self.api_endpoint or not self.api_key:
            logging.warning(
                "Xcitium SOCaaP credentials not configured. Skipping containment."
            )
            return
        payload = {
            "cve_id": evidence.get("cve_id"),
            "affected_hosts": evidence.get("affected_hosts"),
            "active_processes": evidence.get("active_processes"),
            "containment_priority": evidence.get("containment_priority"),
            "evidence_sources": ["SIEM", "RMM", "SBOM"],
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_endpoint}/alerts/containment", json=payload
                )
                response.raise_for_status()
            logging.info(
                f"Successfully sent containment alert for {evidence.get('cve_id')} to Xcitium SOCaaP."
            )
        except httpx.HTTPError as e:
            logging.exception(
                f"Failed to send containment alert to Xcitium SOCaaP: {e}"
            )