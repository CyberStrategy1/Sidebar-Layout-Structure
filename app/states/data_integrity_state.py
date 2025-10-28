import reflex as rx
import logging


class DataIntegrityState(rx.State):
    """State for the Data Integrity Dashboard."""

    is_scanning: bool = False
    scan_results: list[dict[str, str]] = []
    last_scan_time: str = "Never"

    @rx.event(background=True)
    async def run_integrity_scan(self):
        """Simulates running a data integrity scan."""
        async with self:
            self.is_scanning = True
        try:
            import asyncio

            await asyncio.sleep(2)
            results = [
                {
                    "check": "CVSS Score Consistency",
                    "status": "Passed",
                    "details": "All 1,234 records are consistent.",
                },
                {
                    "check": "CPE Format Validation",
                    "status": "Passed",
                    "details": "All 5,678 CPEs are valid.",
                },
                {
                    "check": "Orphaned Vulnerabilities",
                    "status": "Warning",
                    "details": "Found 3 vulnerabilities not linked to any tech stack.",
                },
                {
                    "check": "Duplicate CVE Entries",
                    "status": "Failed",
                    "details": "Found 12 duplicate CVE-2024-xxxx entries.",
                },
            ]
            async with self:
                from datetime import datetime, timezone

                self.scan_results = results
                self.last_scan_time = datetime.now(timezone.utc).strftime(
                    "%Y-%m-%d %H:%M:%S UTC"
                )
                yield rx.toast.success("Data integrity scan completed!")
        except Exception as e:
            logging.exception(f"Data integrity scan failed: {e}")
            async with self:
                yield rx.toast.error("An error occurred during the scan.")
        finally:
            async with self:
                self.is_scanning = False