import reflex as rx
import secrets
import string
import logging
from datetime import datetime, timezone
from app.utils import supabase_client
from app.state import AppState
from app.models import ApiKey


class ApiState(rx.State):
    """Manages API keys, usage, and documentation."""

    api_keys: list[ApiKey] = []
    is_loading: bool = False
    revoking_key_id: str = ""

    def _generate_api_key(self, prefix="apk", length=32) -> str:
        alphabet = string.ascii_letters + string.digits
        key = "".join((secrets.choice(alphabet) for _ in range(length)))
        return f"{prefix}_{key}"

    @rx.event(background=True)
    async def load_api_keys(self):
        """Load API keys for the current organization."""
        async with self:
            self.is_loading = True
            app_state = await self.get_state(AppState)
            org_id = app_state.active_organization_id
        if not org_id:
            async with self:
                self.is_loading = False
            return
        try:
            keys = await supabase_client.get_api_keys_for_org(org_id)
            processed_keys = []
            for key in keys:
                masked = f"{key['key_prefix']}_...{key['key_hash'][-4:]}"
                processed_keys.append(
                    {
                        **key,
                        "masked_key": masked,
                        "full_key": "This would be the full key only on creation",
                    }
                )
            async with self:
                self.api_keys = processed_keys
        except Exception as e:
            logging.exception(f"Failed to load API keys: {e}")
        finally:
            async with self:
                self.is_loading = False

    @rx.event(background=True)
    async def generate_api_key(self, form_data: dict):
        """Generate a new API key and store its hash."""
        key_name = form_data.get("key_name").strip()
        if not key_name:
            yield rx.toast.error("Key name cannot be empty.")
            return
        async with self:
            self.is_loading = True
            app_state = await self.get_state(AppState)
            org_id = app_state.active_organization_id
        if not org_id:
            async with self:
                self.is_loading = False
            yield rx.toast.error("No active organization.")
            return
        try:
            full_key = self._generate_api_key()
            key_prefix, key_body = full_key.split("_")
            key_hash = key_body
            new_key_record = await supabase_client.create_api_key(
                org_id=org_id,
                key_name=key_name,
                key_prefix=key_prefix,
                key_hash=key_hash,
            )
            if new_key_record:
                masked = f"{new_key_record['key_prefix']}_...{new_key_record['key_hash'][-4:]}"
                new_key_display = {
                    **new_key_record,
                    "masked_key": masked,
                    "full_key": full_key,
                }
                async with self:
                    self.api_keys.insert(0, new_key_display)
                yield rx.toast.success(
                    f"API Key '{key_name}' created. Copy it now, you won't see it again."
                )
            else:
                raise Exception("Failed to get record back from DB")
        except Exception as e:
            logging.exception(f"Failed to generate API key: {e}")
            yield rx.toast.error("Failed to create API key.")
        finally:
            async with self:
                self.is_loading = False

    @rx.event(background=True)
    async def revoke_api_key(self, key_id: str):
        """Revoke an API key by its ID."""
        async with self:
            self.revoking_key_id = str(key_id)
        try:
            success = await supabase_client.revoke_api_key(key_id)
            if success:
                async with self:
                    self.api_keys = [k for k in self.api_keys if k["id"] != key_id]
                yield rx.toast.success("API Key revoked successfully.")
            else:
                yield rx.toast.error("Failed to revoke API key.")
        except Exception as e:
            logging.exception(f"Error revoking API key: {e}")
        finally:
            async with self:
                self.revoking_key_id = ""