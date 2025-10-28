import reflex as rx
from app.state import AppState
from app.states.auth_state import AuthState
from app.utils import supabase_client
import logging
from typing import Optional
from datetime import datetime, timezone, timedelta

EXPORT_FORMATS_BY_TIER = {
    "free": ["csv", "json"],
    "pro": ["csv", "json", "excel", "pdf", "slack"],
    "enterprise": ["csv", "json", "excel", "pdf", "jira", "servicenow", "slack"],
    "white_label": ["csv", "json", "excel", "pdf", "jira", "servicenow", "slack"],
}
EXPORT_LIMITS_BY_TIER = {"free": 5, "pro": 50, "enterprise": -1}


class ReportingState(rx.State):
    """State to manage the enterprise reporting feature."""

    reports: list[dict] = []
    selected_report: Optional[dict] = None
    report_cves: list[dict] = []
    is_loading: bool = False
    is_exporting: bool = False
    error_message: str = ""
    success_message: str = ""
    available_export_formats: list[str] = []
    export_history: list[dict] = []
    subscription_tier: str = "free"
    show_create_dialog: bool = False
    show_add_cves_dialog: bool = False
    new_report_name: str = ""
    new_report_description: str = ""
    new_report_type: str = "vulnerability"
    selected_cves_for_report: list[str] = []

    @rx.event
    def set_show_create_dialog(self, value: bool):
        """Set the visibility of the create report dialog."""
        self.show_create_dialog = value

    @rx.var
    def export_formats_by_tier(self) -> dict[str, list[str]]:
        """Returns the export format matrix."""
        return EXPORT_FORMATS_BY_TIER

    @rx.event
    def can_export_format(self, format: str) -> bool:
        """Checks if the current user's tier can use a specific export format."""
        return format in self.available_export_formats

    @rx.var
    def total_reports_count(self) -> int:
        """Returns the total number of reports for the organization."""
        return len(self.reports)

    @rx.var
    def recent_exports_count(self) -> int:
        """Returns the count of exports in the last 24 hours."""
        count = 0
        twenty_four_hours_ago = datetime.now(timezone.utc) - timedelta(days=1)
        for export in self.export_history:
            exported_at = datetime.fromisoformat(export["exported_at"])
            if exported_at > twenty_four_hours_ago:
                count += 1
        return count

    @rx.event(background=True)
    async def fetch_reports(self):
        """Fetch all reports for the current organization."""
        async with self:
            self.is_loading = True
        try:
            async with self:
                app_state = await self.get_state(AppState)
            if not app_state.active_organization_id:
                async with self:
                    self.error_message = "No active organization selected."
                    self.is_loading = False
                return
            reports_data = await supabase_client.get_reports_for_organization(
                app_state.active_organization_id
            )
            async with self:
                self.reports = reports_data
            await self.get_available_export_formats()
        except Exception as e:
            logging.exception(f"Error fetching reports: {e}")
            async with self:
                self.error_message = "Failed to fetch reports."
        finally:
            async with self:
                self.is_loading = False

    @rx.event(background=True)
    async def create_report(self, form_data: dict):
        """Create a new report."""
        name = form_data.get("name", "").strip()
        description = form_data.get("description", "").strip()
        report_type = self.new_report_type
        async with self:
            if not name:
                self.error_message = "Report name cannot be empty."
                yield rx.toast.error("Report name cannot be empty.")
                return
            if any((report["name"] == name for report in self.reports)):
                self.error_message = f"A report with the name '{name}' already exists."
                yield rx.toast.error(self.error_message)
                return
            self.is_loading = True
            self.error_message = ""
        try:
            async with self:
                app_state = await self.get_state(AppState)
                auth_state = await self.get_state(AuthState)
            org_id = app_state.active_organization_id
            creator_id = auth_state.user_id
            if not org_id or not creator_id:
                raise ValueError("Organization or User ID is missing.")
            new_report = await supabase_client.create_report(
                org_id, creator_id, name, description, report_type
            )
            if new_report:
                async with self:
                    self.show_create_dialog = False
                    self.new_report_name = ""
                    self.new_report_description = ""
                yield ReportingState.fetch_reports
                yield rx.toast.success(f"Report '{name}' created successfully!")
            else:
                raise Exception("Report creation returned no data.")
        except Exception as e:
            logging.exception(f"Failed to create report: {e}")
            async with self:
                self.error_message = "An error occurred while creating the report."
            yield rx.toast.error(self.error_message)
        finally:
            async with self:
                self.is_loading = False

    @rx.event(background=True)
    async def get_available_export_formats(self):
        """Get available export formats based on subscription tier."""
        try:
            async with self:
                app_state = await self.get_state(AppState)
            if not app_state.active_organization_id:
                return
            org_data = await supabase_client.get_organization_details(
                app_state.active_organization_id
            )
            tier = "free"
            if org_data and org_data.get("subscription_tier"):
                tier = org_data["subscription_tier"]
            async with self:
                self.subscription_tier = tier
                self.available_export_formats = EXPORT_FORMATS_BY_TIER.get(tier, [])
        except Exception as e:
            logging.exception(f"Failed to get subscription tier: {e}")
            async with self:
                self.available_export_formats = EXPORT_FORMATS_BY_TIER["free"]