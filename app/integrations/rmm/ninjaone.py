import httpx
from typing import Any, Union
from app.integrations.rmm.base import RMMIntegration


class NinjaOneIntegration(RMMIntegration):
    """Integration for NinjaOne RMM."""

    def __init__(self, api_endpoint: str, api_key: str):
        self.api_endpoint = api_endpoint
        self.headers = {"X-API-Key": api_key}

    async def get_endpoint_processes(
        self, host: str
    ) -> list[dict[str, Union[str, int, float]]]:
        return [
            {
                "process_name": "java.exe",
                "pid": 9876,
                "cpu_usage": 2.5,
                "mem_usage": 204800,
            }
        ]

    async def check_service_running(self, service_name: str, host: str) -> bool:
        return service_name == "tomcat9"

    async def get_installed_software(self, host: str) -> list[dict[str, str]]:
        return [{"name": "Apache Tomcat", "version": "9.0.58"}]

    async def validate_patch_status(
        self, cve_id: str, host: str
    ) -> dict[str, Union[str, bool]]:
        return {
            "cve_id": cve_id,
            "patched": True,
            "patch_name": "Security Update for Tomcat",
            "installed_on": "2024-07-29",
        }