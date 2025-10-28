import reflex as rx
from app.states.auth_state import AuthState
from app.utils import supabase_client, sbom_parser
import logging


class OnboardingState(rx.State):
    """State to manage the multi-step onboarding process."""

    is_loading: bool = False
    is_uploading: bool = False
    error_message: str = ""
    current_step: int = 1
    full_name: str = ""
    job_title: str = ""
    org_name: str = ""
    industry: str = ""
    company_size: str = ""
    cloud_provider: str = ""
    ip_ranges: str = ""
    sbom_file_name: str | None = None
    deployment_env: str = ""
    compliance_reqs: list[str] = []
    tech_stack: list[str] = []
    new_tech_item: str = ""
    risk_appetite: str = "moderate"

    @rx.event(background=True)
    async def on_load(self):
        """Check if the user has completed onboarding."""
        async with self:
            auth_state = await self.get_state(AuthState)
            if auth_state.is_onboarding_complete:
                return rx.redirect("/")
            self.current_step = auth_state.onboarding_step

    @rx.event(background=True)
    async def handle_step_1(self, form_data: dict):
        """Process step 1, create org, and move to step 2."""
        async with self:
            self.is_loading = True
            self.full_name = form_data["full_name"]
            self.job_title = form_data["job_title"]
            self.org_name = form_data["org_name"]
        try:
            async with self:
                auth_state = await self.get_state(AuthState)
                if not auth_state.user_id:
                    raise Exception("User is not authenticated.")
                org_id = await supabase_client.create_organization(self.org_name)
                if not org_id:
                    raise Exception("Failed to create organization.")
                await supabase_client.create_membership(
                    auth_state.user_id, org_id, "owner"
                )
                await supabase_client.update_user_profile(
                    auth_state.user_id, self.full_name, self.job_title
                )
                auth_state.onboarding_step = 2
                self.current_step = 2
                self.is_loading = False
        except Exception as e:
            logging.exception(f"Onboarding Step 1 failed: {e}")
            async with self:
                self.error_message = f"An error occurred: {str(e)}"
                self.is_loading = False

    @rx.event(background=True)
    async def handle_step_2(self, form_data: dict):
        """Process step 2, save context, and move to step 3."""
        async with self:
            self.is_loading = True
            self.cloud_provider = form_data["cloud_provider"]
            self.ip_ranges = form_data.get("ip_ranges", "")
        try:
            async with self:
                auth_state = await self.get_state(AuthState)
                memberships = await supabase_client.get_user_memberships()
                if not memberships or not memberships.data:
                    raise Exception("No organization membership found for user.")
                org_id = memberships.data[0]["organization_id"]
                context_data = {
                    "organization_id": org_id,
                    "cloud_provider": self.cloud_provider,
                    "ip_ranges": self.ip_ranges,
                    "sbom_file": self.sbom_file_name,
                }
                await supabase_client.upsert_organization_context(context_data)
                auth_state.onboarding_step = 3
                self.current_step = 3
                self.is_loading = False
        except Exception as e:
            logging.exception(f"Onboarding Step 2 failed: {e}")
            async with self:
                self.error_message = f"An error occurred: {str(e)}"
                self.is_loading = False

    @rx.event
    async def handle_sbom_upload(self, files: list[rx.UploadFile]):
        if not files:
            return rx.toast.error("No SBOM file selected.")
        self.is_uploading = True
        try:
            file = files[0]
            upload_data = await file.read()
            upload_dir = rx.get_upload_dir()
            upload_dir.mkdir(parents=True, exist_ok=True)
            file_path = upload_dir / file.name
            with file_path.open("wb") as f:
                f.write(upload_data)
            self.sbom_file_name = file.name
            components = sbom_parser.parse_sbom(upload_data, file.name)
            self.tech_stack.extend(
                [c["name"] for c in components if c["name"] not in self.tech_stack]
            )
            self.is_uploading = False
            return rx.toast.success(
                f"Processed SBOM and extracted {len(components)} components."
            )
        except Exception as e:
            logging.exception(f"SBOM upload/processing failed: {e}")
            self.is_uploading = False
            return rx.toast.error(f"SBOM processing failed: {e}")

    @rx.event
    def add_tech_item(self):
        item = self.new_tech_item.strip()
        if item and item not in self.tech_stack:
            self.tech_stack.append(item)
            self.new_tech_item = ""

    @rx.event
    async def complete_onboarding(self):
        if len(self.tech_stack) < 3:
            self.error_message = "Please add at least 3 technologies."
            return
        self.is_loading = True
        try:
            memberships = await supabase_client.get_user_memberships()
            if not memberships or not memberships.data:
                raise Exception("No organization membership found for user.")
            org_id = memberships.data[0]["organization_id"]
            await supabase_client.update_organization_tech_stack(
                org_id, self.tech_stack
            )
            auth_state = await self.get_state(AuthState)
            auth_state.onboarding_step = 4
            auth_state.is_first_login = False
            yield rx.redirect("/")
        except Exception as e:
            logging.exception(f"Onboarding completion failed: {e}")
            self.error_message = f"An error occurred: {e}"
        finally:
            self.is_loading = False