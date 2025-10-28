import reflex as rx
from typing import TypedDict
import httpx
import logging
from datetime import datetime, timedelta, timezone
import httpx
import os
import time
from app.utils import supabase_client
from app.models import Membership
from datetime import datetime
import random


class NavItem(TypedDict):
    label: str
    icon: str
    href: str


class UserProfile(TypedDict):
    full_name: str
    avatar_url: str


from datetime import datetime


class AppState(rx.State):
    """The base state for the entire app."""

    is_loading: bool = False
    last_successful_run_time: datetime | None = None
    is_refresh_on_cooldown: bool = False
    unenriched_cves: list[dict] = []
    enrichment_analysis_results: list[dict] = []
    gaps_found_count: int = 0
    gap_analysis_in_progress: bool = False
    tech_stack: list[str] = ["PostgreSQL", "Windows Server"]
    new_tech_stack_item: str = ""
    memberships: list[Membership] = []
    active_organization_id: str | None = None
    user_profile: UserProfile = {"full_name": "", "avatar_url": ""}
    scanner_view_cves: list[dict] = [
        {
            "CVE ID": "CVE-2024-0001",
            "Vendor": "apache",
            "Product": "Apache HTTP Server",
            "Version": "2.4.58",
        },
        {
            "CVE ID": "CVE-2024-0002",
            "Vendor": "microsoft",
            "Product": "Windows Server",
            "Version": "2019",
        },
        {
            "CVE ID": "CVE-2024-0003",
            "Vendor": "postgresql",
            "Product": "PostgreSQL",
            "Version": "14.0",
        },
        {
            "CVE ID": "CVE-2024-0004",
            "Vendor": "oracle",
            "Product": "Java SE",
            "Version": "8u391",
        },
        {
            "CVE ID": "CVE-2024-0005",
            "Vendor": "cisco",
            "Product": "IOS XE",
            "Version": "17.9.1",
        },
    ]

    @rx.var
    def active_org_plan(self) -> str:
        """Returns the subscription plan for the active organization."""
        if not self.memberships or not self.active_organization_id:
            return "free"
        for membership in self.memberships:
            if membership["organization"]["id"] == self.active_organization_id:
                org_name = membership["organization"]["name"].lower()
                if "enterprise" in org_name:
                    return "enterprise"
                if "pro" in org_name:
                    return "pro"
        return "free"

    @rx.var
    def can_export_csv(self) -> bool:
        return self.active_org_plan in ["pro", "enterprise", "msp"]

    @rx.var
    def can_export_pdf(self) -> bool:
        return self.active_org_plan in ["pro", "enterprise", "msp"]

    @rx.var
    def can_use_api_access(self) -> bool:
        return self.active_org_plan in ["enterprise", "msp"]

    @rx.var
    def can_use_sso(self) -> bool:
        return self.active_org_plan in ["enterprise", "msp"]

    @rx.var
    def can_use_ai_analysis(self) -> bool:
        return self.active_org_plan in ["pro", "enterprise", "msp"]

    @rx.var
    def can_have_unlimited_members(self) -> bool:
        return self.active_org_plan in ["enterprise", "msp"]

    @rx.var
    def can_use_secure_sharing(self) -> bool:
        return self.active_org_plan in ["enterprise", "msp"]

    @rx.var
    def top_10_unenriched_cves(self) -> list[dict]:
        """Returns the top 10 unenriched CVEs for the live view."""
        return self.unenriched_cves[:10]

    @rx.var
    def cooldown_tooltip_message(self) -> str:
        """Returns the tooltip message for the refresh button during cooldown."""
        return "Data refreshed less than 5 minutes ago. No need to run again."

    @rx.event
    def switch_organization(self, organization_id: str):
        """Switch the active organization and refetch data."""
        self.active_organization_id = organization_id
        return AppState.fetch_and_filter_nvd_data

    @rx.event
    def add_tech_stack_item(self, form_data: dict):
        """Add a new item to the tech stack."""
        new_item = form_data.get("new_tech_stack_item")
        if new_item and new_item not in self.tech_stack:
            self.tech_stack.append(new_item)

    @rx.event
    def add_tech_item(self):
        """Add a new item to the tech stack from the input field."""
        item_to_add = self.new_tech_stack_item.strip()
        if item_to_add and item_to_add not in self.tech_stack:
            self.tech_stack.append(item_to_add)
            self.new_tech_stack_item = ""
            return AppState.fetch_and_filter_nvd_data

    @rx.event
    def remove_tech_item(self, item: str):
        """Remove an item from the tech stack."""
        self.tech_stack.remove(item)
        return AppState.fetch_and_filter_nvd_data

    @rx.var
    def cves_awaiting_enrichment_count(self) -> int:
        """Returns the count of CVEs awaiting enrichment."""
        return len(self.unenriched_cves)

    @rx.var
    def my_stack_gaps_count(self) -> int:
        """Returns the count of critical gaps in the user's tech stack."""
        count = 0
        tech_stack_lower = [tech.lower() for tech in self.tech_stack]
        for cve in self.unenriched_cves:
            description = cve.get("Product Description", "").lower()
            if any((tech in description for tech in tech_stack_lower)):
                count += 1
        return count

    @rx.var
    def average_enrichment_lag(self) -> int:
        """Returns the average enrichment lag in days (static for now)."""
        return 28

    @rx.var
    def cves_by_vendor(self) -> list[dict[str, str | int]]:
        """Returns the top 5 vendors by CVE count."""
        vendor_counts = {}
        for cve in self.unenriched_cves:
            vendor = cve.get("Vendor", "N/A")
            if vendor == "N/A":
                description = cve.get("Product Description", "").lower()
                if "microsoft" in description or "windows" in description:
                    vendor = "Microsoft"
                elif (
                    "apple" in description
                    or "ios" in description
                    or "macos" in description
                ):
                    vendor = "Apple"
                elif (
                    "google" in description
                    or "android" in description
                    or "chrome" in description
                ):
                    vendor = "Google"
                elif "linux" in description:
                    vendor = "Linux"
                else:
                    vendor = "Other"
            vendor_counts[vendor] = vendor_counts.get(vendor, 0) + 1
        sorted_vendors = sorted(
            vendor_counts.items(), key=lambda item: item[1], reverse=True
        )
        top_vendors = sorted_vendors[:5]
        return [{"name": name, "count": count} for name, count in top_vendors]

    @rx.var
    def current_page(self) -> str:
        """Returns the current page path."""
        return self.router.page.path

    @rx.event(background=True)
    async def on_login_load(self):
        """Load user and organization data after login."""
        async with self:
            self.is_loading = True
        try:
            user_response = await supabase_client.get_current_user_with_profile()
            if user_response and user_response.data:
                profile = user_response.data[0]
                async with self:
                    self.user_profile = {
                        "full_name": profile.get("full_name", ""),
                        "avatar_url": profile.get("avatar_url", ""),
                    }
            memberships_response = await supabase_client.get_user_memberships()
            if memberships_response and memberships_response.data is not None:
                async with self:
                    self.memberships = memberships_response.data
                    if self.memberships:
                        self.active_organization_id = self.memberships[0][
                            "organization_id"
                        ]
                        yield AppState.fetch_and_filter_nvd_data
        except Exception as e:
            logging.exception("Error during on_login_load: %s", e)
        finally:
            async with self:
                self.is_loading = False

    async def _insert_gaps_to_supabase(self, gaps: list[dict]):
        """Helper to batch-insert discovered gaps into the Supabase table."""
        if not self.active_organization_id or not gaps:
            return
        records_to_insert = []
        discovered_at = datetime.now(timezone.utc).isoformat()
        for gap in gaps:
            records_to_insert.append(
                {
                    "cve_id": gap["cve_id"],
                    "description": gap["description"],
                    "published_date": gap["published_date"],
                    "last_modified": gap["last_modified"],
                    "missing_cvss": gap["missing_cvss"],
                    "missing_cpe": gap["missing_cpe"],
                    "organization_id": self.active_organization_id,
                    "discovered_at": discovered_at,
                }
            )
        try:
            await supabase_client.insert_vulnerabilities(records_to_insert)
        except Exception as e:
            logging.exception(f"Failed to insert gaps into Supabase: {e}")

    async def _insert_gaps_to_supabase(self, gaps: list[dict]):
        """Helper to batch-insert discovered gaps into the Supabase table."""
        if not self.active_organization_id or not gaps:
            return
        records_to_insert = []
        discovered_at = datetime.now(timezone.utc).isoformat()
        for gap in gaps:
            records_to_insert.append(
                {
                    "cve_id": gap["cve_id"],
                    "description": gap["description"],
                    "published_date": gap["published_date"],
                    "last_modified": gap["last_modified"],
                    "missing_cvss": gap["missing_cvss"],
                    "missing_cpe": gap["missing_cpe"],
                    "organization_id": self.active_organization_id,
                    "discovered_at": discovered_at,
                }
            )
        try:
            await supabase_client.insert_vulnerabilities(records_to_insert)
        except Exception as e:
            logging.exception(f"Failed to insert gaps into Supabase: {e}")

    def _calculate_cvss_gap_score(self, metrics: dict) -> float:
        """Analyzes CVSS data completeness and returns a score from 0-10."""
        if not metrics:
            return 10.0
        score = 0
        if not any(
            (k in metrics for k in ["cvssMetricV31", "cvssMetricV30", "cvssMetricV2"])
        ):
            score += 5.0
        primary_metric = metrics.get("cvssMetricV31", [{}])[0]
        if not primary_metric.get("cvssData", {}).get("baseScore"):
            score += 3.0
        if not primary_metric.get("cvssData", {}).get("vectorString"):
            score += 2.0
        return min(score, 10.0)

    def _calculate_cpe_gap_score(self, configurations: list) -> float:
        """Analyzes CPE data completeness and returns a score from 0-10."""
        if not configurations:
            return 10.0
        total_nodes = 0
        nodes_with_cpe = 0
        for config in configurations:
            nodes = config.get("nodes", [])
            for node in nodes:
                total_nodes += 1
                if any((match.get("criteria") for match in node.get("cpeMatch", []))):
                    nodes_with_cpe += 1
        if total_nodes == 0:
            return 5.0
        completeness_ratio = nodes_with_cpe / total_nodes
        return round((1 - completeness_ratio) * 10, 2)

    def _calculate_reference_quality(self, references: list) -> float:
        """Scores the quality of references from 0-10 based on diversity and source."""
        if not references:
            return 0.0
        score = 0.0
        tags = [ref.get("tags", []) for ref in references]
        flat_tags = [tag for sublist in tags for tag in sublist]
        if "Vendor Advisory" in flat_tags:
            score += 4.0
        if "Third Party Advisory" in flat_tags:
            score += 3.0
        if "Patch" in flat_tags:
            score += 2.0
        if len(references) > 5:
            score += 1.0
        return min(score, 10.0)

    def _match_tech_stack(
        self, description: str, tech_stack: list[str]
    ) -> tuple[bool, int]:
        """Matches a description against the tech stack, returning a boolean and confidence score."""
        if not tech_stack or not description:
            return (False, 0)
        description_lower = description.lower()
        matched_items = [
            item for item in tech_stack if item.lower() in description_lower
        ]
        if not matched_items:
            return (False, 0)
        confidence = min(len(matched_items) * 25, 100)
        return (True, confidence)

    def _calculate_enrichment_velocity(self) -> float:
        """Calculates a mock enrichment velocity in days."""
        return round(random.uniform(5.0, 25.0), 2)

    @rx.event(background=True)
    async def run_gap_analysis_engine(self, organization_id: str | None = None):
        """The core gap analysis engine. Inserts run, fetches data, analyzes, upserts, and updates run."""
        org_id = organization_id or self.active_organization_id
        if not org_id:
            logging.warning("Engine run skipped: No organization ID provided.")
            return
        async with self:
            self.gap_analysis_in_progress = True
        run_id = None
        try:
            run_id = await supabase_client.insert_engine_run(org_id)
            if not run_id:
                raise Exception("Failed to create engine run record.")
            org_details = await supabase_client.get_organization_details(org_id)
            tech_stack = org_details.get("tech_stack", []) if org_details else []
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=30)
            url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?pubStartDate={start_date.strftime('%Y-%m-%dT%H:%M:%S')}&pubEndDate={end_date.strftime('%Y-%m-%dT%H:%M:%S')}&resultsPerPage=2000"
            nvd_api_key = os.getenv("NVD_API_KEY")
            headers = {"apiKey": nvd_api_key} if nvd_api_key else {}
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=60.0)
                response.raise_for_status()
                data = response.json()
            vulnerabilities = data.get("vulnerabilities", [])
            gaps_found = []
            for i, vuln in enumerate(vulnerabilities):
                if i > 0 and i % 50 == 0:
                    yield rx.toast.info(f"Analyzing CVE {i}/{len(vulnerabilities)}...")
                cve = vuln.get("cve", {})
                published_str = cve.get("published")
                last_modified_str = cve.get("lastModified")
                time_gap = -1
                if published_str and last_modified_str:
                    published = datetime.fromisoformat(
                        published_str.replace("Z", "+00:00")
                    )
                    last_modified = datetime.fromisoformat(
                        last_modified_str.replace("Z", "+00:00")
                    )
                    time_gap = (last_modified - published).days
                metrics = cve.get("metrics", {})
                configurations = cve.get("configurations", [])
                references = cve.get("references", [])
                cvss_gap_score = self._calculate_cvss_gap_score(metrics)
                cpe_gap_score = self._calculate_cpe_gap_score(configurations)
                ref_score = self._calculate_reference_quality(references)
                overall_gap = round(
                    cvss_gap_score * 0.4
                    + cpe_gap_score * 0.3
                    + time_gap / 30 * 10 * 0.3,
                    2,
                )
                description = cve.get("descriptions", [{"value": ""}])[0]["value"]
                affects_stack, confidence = self._match_tech_stack(
                    description, tech_stack
                )
                velocity = self._calculate_enrichment_velocity()
                estimated_date = datetime.now(timezone.utc) + timedelta(days=velocity)
                gap_record = {
                    "cve_id": cve.get("id"),
                    "description": description,
                    "published_date": cve.get("published"),
                    "last_modified": cve.get("lastModified"),
                    "time_gap_days": time_gap,
                    "missing_cvss": not any(
                        (
                            key in metrics
                            for key in [
                                "cvssMetricV31",
                                "cvssMetricV30",
                                "cvssMetricV2",
                            ]
                        )
                    ),
                    "missing_cpe": not bool(configurations),
                    "cvss_gap_score": cvss_gap_score,
                    "cpe_gap_score": cpe_gap_score,
                    "reference_quality_score": ref_score,
                    "overall_gap_severity": overall_gap,
                    "affects_org_stack": affects_stack,
                    "stack_match_confidence": confidence,
                    "enrichment_velocity": velocity,
                    "estimated_enrichment_date": estimated_date.isoformat(),
                    "organization_id": org_id,
                    "discovered_at": datetime.now(timezone.utc).isoformat(),
                }
                gaps_found.append(gap_record)
            if gaps_found:
                await supabase_client.upsert_vulnerabilities(gaps_found)
            await supabase_client.update_engine_run(
                run_id, "completed", len(gaps_found)
            )
            if org_id == self.active_organization_id:
                async with self:
                    self.gaps_found_count = len(gaps_found)
        except Exception as e:
            logging.exception(f"Gap analysis engine failed for org {org_id}: {e}")
            if run_id:
                await supabase_client.update_engine_run(run_id, "failed")
        finally:
            if org_id == self.active_organization_id:
                async with self:
                    self.gap_analysis_in_progress = False

    @rx.event(background=True)
    async def manual_refresh_clicked(self):
        """Handles manual refresh request, checks cooldown, and triggers engine."""
        async with self:
            if not self.active_organization_id:
                return
            last_run = await supabase_client.get_last_completed_run(
                self.active_organization_id
            )
            if last_run and last_run.get("run_completed_at"):
                self.last_successful_run_time = datetime.fromisoformat(
                    last_run["run_completed_at"]
                )
                time_since_last_run = (
                    datetime.now(timezone.utc) - self.last_successful_run_time
                )
                if time_since_last_run < timedelta(minutes=5):
                    self.is_refresh_on_cooldown = True
                    yield rx.toast("Please wait 5 minutes before refreshing again.")
                    return
            self.is_refresh_on_cooldown = False
        yield AppState.run_gap_analysis_engine(
            organization_id=self.active_organization_id
        )

    @rx.event(background=True)
    async def fetch_and_filter_nvd_data(self):
        """Fetch and filter CVE data from the NVD API for unenriched CVEs."""
        async with self:
            self.is_loading = True
        start_time_ts = time.time()
        start_time_iso = datetime.now(timezone.utc).isoformat()
        nvd_api_key = os.getenv("NVD_API_KEY")
        headers = {"apiKey": nvd_api_key} if nvd_api_key else {}
        log_data = {"api_name": "NVD API", "start_time": start_time_iso}
        try:
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=90)
            pub_start_date = start_date.strftime("%Y-%m-%dT%H:%M:%S")
            pub_end_date = end_date.strftime("%Y-%m-%dT%H:%M:%S")
            url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?pubStartDate={pub_start_date}&pubEndDate={pub_end_date}&resultsPerPage=2000"
            log_data["endpoint"] = url
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=30.0)
                log_data["status_code"] = response.status_code
                response.raise_for_status()
                data = response.json()
            vulnerabilities = data.get("vulnerabilities", [])
            filtered_results = []
            for vuln in vulnerabilities:
                cve_item = vuln.get("cve", {})
                if cve_item.get("vulnStatus") == "Awaiting Analysis":
                    filtered_results.append(
                        {
                            "CVE ID": cve_item.get("id", "N/A"),
                            "Vendor": "N/A",
                            "Product Description": cve_item.get(
                                "descriptions", [{"value": "N/A"}]
                            )[0]["value"],
                            "Published Date": cve_item.get("published", "N/A"),
                        }
                    )
            async with self:
                self.unenriched_cves = filtered_results
            log_data["status"] = "success"
            log_data["records_fetched"] = len(vulnerabilities)
        except httpx.HTTPStatusError as e:
            logging.exception(f"HTTP error occurred while fetching NVD data: {e}")
            log_data["status"] = "failure"
            log_data["error_message"] = str(e)
        except Exception as e:
            logging.exception(f"An unexpected error occurred: {e}")
            log_data["status"] = "failure"
            log_data["error_message"] = str(e)
        finally:
            end_time_ts = time.time()
            end_time_iso = datetime.now(timezone.utc).isoformat()
            log_data["end_time"] = end_time_iso
            log_data["duration_ms"] = int((end_time_ts - start_time_ts) * 1000)
            await supabase_client.log_api_health(log_data)
            async with self:
                self.is_loading = False

    @rx.event(background=True)
    async def fetch_recent_modified_cves(self):
        """Fetch CVEs modified in the last 30 days and calculate enrichment lag."""
        async with self:
            if not self.active_organization_id:
                logging.warning("Cannot fetch recent CVEs, no active organization.")
                return
            self.is_loading = True
            self.enrichment_analysis_results = []
        try:
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=30)
            start_date_str = start_date.strftime("%Y-%m-%dT%H:%M:%S")
            end_date_str = end_date.strftime("%Y-%m-%dT%H:%M:%S")
            url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?lastModStartDate={start_date_str}&lastModEndDate={end_date_str}"
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                vulnerabilities = data.get("vulnerabilities", [])
                results = []
                for vuln in vulnerabilities:
                    cve_item = vuln.get("cve", {})
                    cve_id = cve_item.get("id", "N/A")
                    published_str = cve_item.get("published")
                    last_modified_str = cve_item.get("lastModified")
                    if published_str and last_modified_str:
                        published_date = datetime.fromisoformat(published_str)
                        last_modified_date = datetime.fromisoformat(last_modified_str)
                        lag = (last_modified_date - published_date).days
                        results.append({"CVE ID": cve_id, "Enrichment Lag (Days)": lag})
                sorted_results = sorted(
                    results, key=lambda x: x["Enrichment Lag (Days)"], reverse=True
                )
            async with self:
                self.enrichment_analysis_results = sorted_results
        except httpx.HTTPStatusError as e:
            logging.exception(f"HTTP error occurred while fetching recent CVEs: {e}")
        except Exception as e:
            logging.exception(
                f"An unexpected error occurred while fetching recent CVEs: {e}"
            )
        finally:
            async with self:
                self.is_loading = False