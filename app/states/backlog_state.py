import reflex as rx
import httpx
import logging
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import asyncio


class BacklogState(rx.State):
    """State for the CVE Backlog Dashboard."""

    is_loading: bool = False
    backlog_cves: list[dict] = []
    backlog_by_month: list[dict] = []
    total_backlog_count: int = 0
    filter_show_kev: bool = False

    @rx.var
    def filtered_backlog_cves(self) -> list[dict]:
        """Filter backlog CVEs based on UI controls."""
        cves_to_filter = self.backlog_cves
        if self.filter_show_kev:
            return [cve for cve in cves_to_filter if cve.get("cisaExploitAdd")]
        return cves_to_filter

    def _process_backlog_data(self):
        """Helper to process raw CVEs into monthly aggregates."""
        monthly_counts = defaultdict(lambda: {"count": 0, "total_days_waiting": 0})
        today = datetime.now(timezone.utc)
        for cve in self.filtered_backlog_cves:
            published_str = cve.get("published", "")
            if published_str:
                try:
                    published_date = datetime.fromisoformat(
                        published_str.replace("Z", "+00:00")
                    )
                    month_key = published_date.strftime("%Y-%m")
                    monthly_counts[month_key]["count"] += 1
                    days_waiting = (today - published_date).days
                    monthly_counts[month_key]["total_days_waiting"] += days_waiting
                except ValueError as e:
                    logging.exception(f"Error parsing date for backlog processing: {e}")
                    continue
        processed_data = []
        for month, data in sorted(monthly_counts.items(), reverse=True):
            avg_days = (
                round(data["total_days_waiting"] / data["count"])
                if data["count"] > 0
                else 0
            )
            processed_data.append(
                {"month": month, "count": data["count"], "avg_days_waiting": avg_days}
            )
        self.backlog_by_month = processed_data
        self.total_backlog_count = len(self.filtered_backlog_cves)

    @rx.event
    def toggle_kev_filter(self, checked: bool):
        self.filter_show_kev = checked
        self._process_backlog_data()

    @rx.event(background=True)
    async def fetch_backlog_data(self):
        """Fetch recent CVEs and filter for 'Awaiting Analysis' status client-side."""
        async with self:
            self.is_loading = True
            self.backlog_cves = []
            self.backlog_by_month = []
            self.total_backlog_count = 0
        try:
            all_cves_awaiting_analysis = []
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=365)
            start_date_str = start_date.strftime("%Y-%m-%dT%H:%M:%S")
            end_date_str = end_date.strftime("%Y-%m-%dT%H:%M:%S")
            start_index = 0
            total_results = 1
            records_processed = 0
            async with httpx.AsyncClient() as client:
                while True:
                    url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?lastModStartDate={start_date_str}&lastModEndDate={end_date_str}&resultsPerPage=2000&startIndex={start_index}"
                    response = await client.get(url, timeout=60.0)
                    if response.status_code != 200:
                        logging.error(
                            f"NVD API returned status {response.status_code}: {response.text}"
                        )
                        yield rx.toast.error(
                            f"NVD API error: {response.status_code}", duration=5000
                        )
                        break
                    data = response.json()
                    vulnerabilities = data.get("vulnerabilities", [])
                    total_results = data.get("totalResults", 0)
                    for vuln in vulnerabilities:
                        cve = vuln.get("cve", {})
                        if cve.get("vulnStatus") == "Awaiting Analysis":
                            all_cves_awaiting_analysis.append(cve)
                    start_index += len(vulnerabilities)
                    records_processed += len(vulnerabilities)
                    yield rx.toast.info(
                        f"Processed {records_processed}/{total_results} records...",
                        duration=2000,
                    )
                    if start_index >= total_results or not vulnerabilities:
                        break
                    await asyncio.sleep(1)
            async with self:
                self.backlog_cves = all_cves_awaiting_analysis
                self._process_backlog_data()
                yield rx.toast.success(
                    f"Found {self.total_backlog_count} CVEs awaiting analysis."
                )
        except httpx.RequestError as e:
            logging.exception(f"Request to NVD API failed: {e}")
            yield rx.toast.error("Failed to connect to NVD API.", duration=5000)
        except Exception as e:
            logging.exception(f"An unexpected error occurred during backlog fetch: {e}")
            yield rx.toast.error("An unexpected error occurred.", duration=5000)
        finally:
            async with self:
                self.is_loading = False