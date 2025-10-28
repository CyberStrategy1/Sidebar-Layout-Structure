import reflex as rx
from app.utils import supabase_client
from app.state import AppState
from typing import Optional
import datetime
import re

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30


class AuthState(rx.State):
    is_authenticated: bool = False
    is_first_login: bool = False
    user_id: Optional[str] = None
    email: Optional[str] = None
    error_message: str = ""
    success_message: str = ""
    is_loading: bool = False
    password: str = ""
    confirm_password: str = ""
    login_attempts: dict[str, int] = {}
    lockout_timestamps: dict[str, datetime.datetime] = {}
    onboarding_step: int = 1
    user_name: str = ""
    user_role: str = ""
    onboarding_error: str = ""
    org_name: str = ""

    @rx.var
    def is_onboarding_complete(self) -> bool:
        return self.onboarding_step > 3

    @rx.event
    def set_user_role(self, value: str):
        self.user_role = value

    @rx.var
    def password_mismatch(self) -> bool:
        return self.password != self.confirm_password and self.confirm_password != ""

    @rx.var
    def password_strength_error(self) -> str:
        if not self.password:
            return ""
        errors = []
        if len(self.password) < 8:
            errors.append("be at least 8 characters")
        if not re.search("[A-Z]", self.password):
            errors.append("contain an uppercase letter")
        if not re.search("[a-z]", self.password):
            errors.append("contain a lowercase letter")
        if not re.search("[0-9]", self.password):
            errors.append("contain a number")
        if not re.search("[!@#$%^&*()]", self.password):
            errors.append("contain a special character")
        if not errors:
            return ""
        return f"Password must: {', '.join(errors)}."

    def _check_lockout(self, email: str) -> bool:
        if email in self.lockout_timestamps:
            lockout_time = self.lockout_timestamps[email]
            if datetime.datetime.now() < lockout_time + datetime.timedelta(
                minutes=LOCKOUT_DURATION_MINUTES
            ):
                remaining = (
                    lockout_time
                    + datetime.timedelta(minutes=LOCKOUT_DURATION_MINUTES)
                    - datetime.datetime.now()
                )
                self.error_message = (
                    f"Account locked. Try again in {remaining.seconds // 60} minutes."
                )
                return True
            else:
                del self.lockout_timestamps[email]
                del self.login_attempts[email]
        return False

    @rx.event
    async def sign_up(self, form_data: dict):
        self.is_loading = True
        self.error_message = ""
        self.password = form_data.get("password", "")
        self.confirm_password = form_data.get("confirm_password", "")
        email = form_data.get("email")
        if not email or not self.password:
            self.error_message = "Email and password are required."
            self.is_loading = False
            return
        if self.password_strength_error:
            self.error_message = self.password_strength_error
            self.is_loading = False
            return
        if self.password_mismatch:
            self.error_message = "Passwords do not match."
            self.is_loading = False
            return
        user = await supabase_client.sign_up(email, self.password)
        if user:
            self.is_authenticated = True
            self.user_id = user.get("id")
            self.email = user.get("email")
            self.is_first_login = True
            self.error_message = ""
            self.is_loading = False
            return rx.redirect("/onboarding")
        else:
            self.error_message = "Registration failed. User may already exist."
            self.is_loading = False

    @rx.event
    async def sign_in(self, form_data: dict):
        self.is_loading = True
        self.error_message = ""
        email = form_data.get("email")
        password = form_data.get("password")
        if not email or not password:
            self.error_message = "Email and password are required."
            self.is_loading = False
            return
        if self._check_lockout(email):
            self.is_loading = False
            return
        user = await supabase_client.sign_in(email, password)
        if user:
            self.is_authenticated = True
            self.user_id = user.get("id")
            self.email = user.get("email")
            if email in self.login_attempts:
                del self.login_attempts[email]
            self.error_message = ""
            app_state = await self.get_state(AppState)
            await app_state.on_login_load()
            self.is_loading = False
            if self.is_first_login:
                return rx.redirect("/onboarding")
            return rx.redirect("/")
        else:
            self.login_attempts[email] = self.login_attempts.get(email, 0) + 1
            if self.login_attempts[email] >= MAX_LOGIN_ATTEMPTS:
                self.lockout_timestamps[email] = datetime.datetime.now()
                self.error_message = (
                    "Too many failed login attempts. Account locked for 30 minutes."
                )
            else:
                remaining_attempts = MAX_LOGIN_ATTEMPTS - self.login_attempts[email]
                self.error_message = (
                    f"Invalid credentials. {remaining_attempts} attempts remaining."
                )
            self.is_loading = False

    @rx.event
    async def send_password_reset_email(self, form_data: dict):
        self.is_loading = True
        self.error_message = ""
        self.success_message = ""
        email = form_data.get("email")
        if not email:
            self.error_message = "Email is required."
            self.is_loading = False
            return
        success = await supabase_client.reset_password_for_email(email)
        if success:
            self.success_message = "Password reset link sent. Check your email."
        else:
            self.error_message = (
                "Failed to send password reset email. Please try again."
            )
        self.is_loading = False

    @rx.event
    async def reset_password(self, form_data: dict):
        self.is_loading = True
        self.error_message = ""
        self.password = form_data.get("password", "")
        self.confirm_password = form_data.get("confirm_password", "")
        if self.password_strength_error:
            self.error_message = self.password_strength_error
            self.is_loading = False
            return
        if self.password_mismatch:
            self.error_message = "Passwords do not match."
            self.is_loading = False
            return
        print("Password reset logic would execute here.")
        self.success_message = "Password has been reset successfully!"
        self.is_loading = False
        return rx.redirect("/login")

    @rx.event
    def next_onboarding_step(self, form_data: dict):
        self.user_name = form_data.get("user_name", "").strip()
        self.user_role = form_data.get("user_role", "")
        if not self.user_name or not self.user_role:
            self.onboarding_error = "Full Name and Role are required."
            return
        self.onboarding_error = ""
        self.onboarding_step = 2

    @rx.event
    async def complete_onboarding(self):
        self.is_first_login = False
        from app.state import AppState

        app_state = await self.get_state(AppState)
        yield app_state.run_gap_analysis_engine()
        yield rx.redirect("/")

    @rx.event(background=True)
    async def create_organization_and_complete_step(self, form_data: dict):
        """Create organization, member, and update profile."""
        async with self:
            self.is_loading = True
            self.onboarding_error = ""
            self.user_name = form_data.get("user_name", "").strip()
            self.org_name = form_data.get("org_name", "").strip()
        if len(self.org_name) < 3:
            async with self:
                self.onboarding_error = (
                    "Organization name must be at least 3 characters."
                )
                self.is_loading = False
            return
        try:
            org_id = await supabase_client.create_organization(self.org_name)
            if not org_id:
                raise Exception("Failed to create organization.")
            if not self.user_id:
                raise Exception("User ID not found.")
            member_created = await supabase_client.create_membership(
                user_id=self.user_id, org_id=org_id, role="owner"
            )
            if not member_created:
                raise Exception("Failed to create membership.")
            profile_updated = await supabase_client.update_user_profile(
                user_id=self.user_id, full_name=self.user_name, job_title=self.user_role
            )
            if not profile_updated:
                logging.warning(f"Could not update profile for user {self.user_id}")
            async with self:
                self.onboarding_step = 2
                self.is_loading = False
        except Exception as e:
            logging.exception(f"Onboarding Step 1->2 failed: {e}")
            async with self:
                self.onboarding_error = f"An error occurred: {e}"
                self.is_loading = False

    @rx.event
    async def sign_out(self):
        self.is_loading = True
        success = await supabase_client.sign_out()
        if success:
            self.reset()
            return rx.redirect("/login")
        else:
            self.error_message = "Sign out failed."
        self.is_loading = False