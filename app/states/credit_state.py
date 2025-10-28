import reflex as rx
import stripe
import os
import logging
from app.states.auth_state import AuthState
from app.utils import supabase_client

CREDIT_PACKAGES = {
    "100": {
        "name": "Starter Pack",
        "price_id": os.getenv("STRIPE_CREDIT_100_PRICE_ID"),
        "credits": 100,
        "price": 10,
    },
    "500": {
        "name": "Pro Pack",
        "price_id": os.getenv("STRIPE_CREDIT_500_PRICE_ID"),
        "credits": 500,
        "price": 40,
    },
    "1000": {
        "name": "Business Pack",
        "price_id": os.getenv("STRIPE_CREDIT_1000_PRICE_ID"),
        "credits": 1000,
        "price": 70,
    },
}


class CreditState(rx.State):
    """Manages AI credit purchasing and usage history."""

    is_loading: bool = False
    error_message: str = ""
    usage_history: list[dict] = []
    selected_package: str = ""

    @rx.event
    async def create_credit_checkout_session(self, package_key: str):
        """Create a Stripe Checkout session to purchase AI credits."""
        self.is_loading = True
        self.error_message = ""
        self.selected_package = package_key
        try:
            auth_state = await self.get_state(AuthState)
            if not auth_state.is_authenticated or not auth_state.email:
                self.error_message = "User not authenticated. Please sign in."
                self.is_loading = False
                return rx.redirect("/login")
            package_details = CREDIT_PACKAGES.get(package_key)
            if not package_details or not package_details.get("price_id"):
                self.error_message = f"Invalid credit package '{package_key}' selected."
                self.is_loading = False
                return
            stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
            checkout_session = stripe.checkout.Session.create(
                line_items=[{"price": package_details["price_id"], "quantity": 1}],
                mode="payment",
                success_url="http://localhost:3000/ai-config?credit_purchase=success",
                cancel_url="http://localhost:3000/ai-config",
                customer_email=auth_state.email,
                metadata={
                    "user_id": auth_state.user_id,
                    "credits_to_add": package_details["credits"],
                },
            )
            if checkout_session.url:
                self.is_loading = False
                return rx.redirect(checkout_session.url)
            else:
                self.error_message = "Could not create a checkout session."
        except Exception as e:
            logging.exception(f"Error creating Stripe credit checkout: {e}")
            self.error_message = "An unexpected error occurred."
        finally:
            self.is_loading = False

    @rx.event(background=True)
    async def fetch_usage_history(self):
        """Fetches the LLM usage history for the current organization."""
        async with self:
            pass