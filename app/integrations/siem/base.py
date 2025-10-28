from abc import ABC, abstractmethod
from typing import Any, Union


class SIEMIntegration(ABC):
    """Abstract base class for SIEM integrations."""

    @abstractmethod
    async def query_logs(
        self, query: str, time_range: dict[str, str]
    ) -> list[dict[str, str]]:
        """Execute a raw query against the SIEM."""
        pass

    @abstractmethod
    async def check_process_activity(self, process_name: str, host: str) -> bool:
        """Check for recent activity of a specific process on a host."""
        pass

    @abstractmethod
    async def get_service_status(self, service_name: str, host: str) -> dict[str, str]:
        """Get the status of a specific service on a host."""
        pass

    @abstractmethod
    async def search_events(self, cve_id: str, component: str) -> list[dict[str, str]]:
        """Search for events related to a CVE or component."""
        pass