from abc import ABC, abstractmethod
from typing import Any, Union


class RMMIntegration(ABC):
    """Abstract base class for RMM integrations."""

    @abstractmethod
    async def get_endpoint_processes(
        self, host: str
    ) -> list[dict[str, Union[str, int, float]]]:
        """Get a list of running processes on a specific host."""
        pass

    @abstractmethod
    async def check_service_running(self, service_name: str, host: str) -> bool:
        """Check if a specific service is running on a host."""
        pass

    @abstractmethod
    async def get_installed_software(self, host: str) -> list[dict[str, str]]:
        """Get a list of installed software on a host."""
        pass

    @abstractmethod
    async def validate_patch_status(
        self, cve_id: str, host: str
    ) -> dict[str, Union[str, bool]]:
        """Validate the patch status for a given CVE on a host."""
        pass