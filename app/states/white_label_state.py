import reflex as rx
import logging
from app.utils import supabase_client
from app.state import AppState
import re


class WhiteLabelState(rx.State):
    """Manages the white-label configuration for an organization."""

    is_loading: bool = False
    company_name: str = "SaaS App"
    dashboard_title: str = "Main Dashboard"
    logo_url: str = "/icon.svg"
    favicon_url: str = "/favicon.ico"
    primary_color: str = "#2E3A4D"
    secondary_color: str = "#38B2AC"
    accent_color: str = "#3b82f6"
    custom_domain: str = ""
    footer_text: str = "© 2024 Aperture. All rights reserved."
    support_url: str = "/support"
    terms_url: str = "/terms"
    privacy_url: str = "/privacy"
    custom_css: str = ""
    show_preview: bool = False
    error_message: str = ""

    def _validate_urls(self):
        urls_to_validate = {
            "Logo URL": self.logo_url,
            "Favicon URL": self.favicon_url,
            "Support URL": self.support_url,
            "Terms URL": self.terms_url,
            "Privacy URL": self.privacy_url,
        }
        for name, url in urls_to_validate.items():
            if url and (not re.match("^(https?:\\/\\/|\\/)", url)):
                self.error_message = f"Invalid {name}. Must be a valid URL or path."
                return False
        self.error_message = ""
        return True

    @rx.event(background=True)
    async def load_white_label_config(self):
        """Load the white-label configuration for the active organization."""
        async with self:
            self.is_loading = True
            app_state = await self.get_state(AppState)
            org_id = app_state.active_organization_id
        if not org_id:
            async with self:
                self.is_loading = False
                self.company_name = "SaaS App"
                self.dashboard_title = "Main Dashboard"
                self.logo_url = "/icon.svg"
            return
        try:
            config = await supabase_client.get_white_label_config(org_id)
            if config:
                async with self:
                    for key, value in config.items():
                        if hasattr(self, key) and value is not None:
                            setattr(self, key, value)
            else:
                org_details = await supabase_client.get_organization_details(org_id)
                if org_details:
                    async with self:
                        self.company_name = org_details.get("name", "SaaS App")
        except Exception as e:
            logging.exception(f"Failed to load white-label config: {e}")
        finally:
            async with self:
                self.is_loading = False

    @rx.event(background=True)
    async def save_white_label_config(self):
        """Save the white-label configuration."""
        async with self:
            if not self._validate_urls():
                yield rx.toast.error(self.error_message)
                return
            self.is_loading = True
            app_state = await self.get_state(AppState)
            org_id = app_state.active_organization_id
        if not org_id:
            yield rx.toast.error("No active organization to save config for.")
            async with self:
                self.is_loading = False
            return
        try:
            config_data = {
                "organization_id": org_id,
                "company_name": self.company_name,
                "dashboard_title": self.dashboard_title,
                "logo_url": self.logo_url,
                "favicon_url": self.favicon_url,
                "primary_color": self.primary_color,
                "secondary_color": self.secondary_color,
                "accent_color": self.accent_color,
                "custom_domain": self.custom_domain,
                "footer_text": self.footer_text,
                "support_url": self.support_url,
                "terms_url": self.terms_url,
                "privacy_url": self.privacy_url,
                "custom_css": self.custom_css,
            }
            success = await supabase_client.save_white_label_config(org_id, config_data)
            if success:
                yield rx.toast.success("White-label configuration saved!")
            else:
                yield rx.toast.error("Failed to save configuration.")
        except Exception as e:
            logging.exception(f"Failed to save white-label config: {e}")
            yield rx.toast.error("An unexpected error occurred.")
        finally:
            async with self:
                self.is_loading = False

    @rx.event
    def reset_to_defaults(self):
        """Reset all settings to their default values."""
        self.company_name = "SaaS App"
        self.dashboard_title = "Main Dashboard"
        self.logo_url = "/icon.svg"
        self.favicon_url = "/favicon.ico"
        self.primary_color = "#2E3A4D"
        self.secondary_color = "#38B2AC"
        self.accent_color = "#3b82f6"
        self.custom_domain = ""
        self.footer_text = "© 2024 Aperture. All rights reserved."
        self.support_url = "/support"
        self.terms_url = "/terms"
        self.privacy_url = "/privacy"
        self.custom_css = ""
        return rx.toast.info("Settings have been reset to default.")

    @rx.event
    def toggle_preview(self):
        self.show_preview = not self.show_preview