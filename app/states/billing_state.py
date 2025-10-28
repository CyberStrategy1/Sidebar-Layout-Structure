import reflex as rx
import stripe
import os
import logging
from app.states.auth_state import AuthState
from app.utils import supabase_client

STRIPE_PLANS = {
    "free": {
        "name": "Free",
        "price_id": None,
        "price": 0,
        "features": [
            "5 CVE analyses/month",
            "Basic dashboard access",
            "1 user seat",
            "7-day data retention",
        ],
    },
    "starter": {
        "name": "Starter",
        "price_id": os.getenv("STRIPE_STARTER_PRICE_ID"),
        "price": 29,
        "features": [
            "100 CVE analyses/month",
            "Email alerts",
            "3 user seats",
            "CSV exports",
        ],
    },
    "pro": {
        "name": "Pro Tier",
        "price_id": os.getenv("STRIPE_PRO_PRICE_ID", "price_1SLalACREXcxM3Q3I43WQ1G1"),
        "price": 99,
        "features": [
            "Unlimited CVE analyses",
            "AI analysis (500 credits/mo)",
            "Slack/Jira integrations",
            "10 user seats",
            "PDF reports",
        ],
    },
    "enterprise": {
        "name": "Enterprise Tier",
        "price_id": os.getenv(
            "STRIPE_ENTERPRISE_PRICE_ID", "price_1SLalACREXcxM3Q3P8K9u9VP"
        ),
        "price": 499,
        "features": [
            "All Pro features",
            "SAML/SSO integration",
            "API Access & Audit Logs",
            "Dedicated support & SLA",
            "Unlimited user seats",
        ],
    },
    "white_label": {
        "name": "White Label",
        "price_id": None,
        "price": "Custom",
        "features": [
            "Full rebranding control",
            "Custom domain",
            "Dedicated infrastructure option",
            "Reseller tools",
        ],
    },
}


class BillingState(rx.State):
    """Manages billing, subscriptions, and Stripe interactions."""

    selected_package: str = ""
    is_loading: bool = False
    error_message: str = ""
    selected_plan: str = ""
    show_annual_pricing: bool = False

    @rx.event
    def toggle_pricing_period(self):
        """Toggle between monthly and annual pricing views."""
        self.show_annual_pricing = not self.show_annual_pricing

    @rx.event
    async def create_checkout_session(self, plan: str):
        """Create a Stripe Checkout session for the selected plan and redirect the user."""
        self.is_loading = True
        self.error_message = ""
        self.selected_plan = plan
        try:
            auth_state = await self.get_state(AuthState)
            if not auth_state.is_authenticated or not auth_state.email:
                self.error_message = "User not authenticated. Please sign in."
                self.is_loading = False
                return rx.redirect("/login")
            price_id = STRIPE_PLANS.get(plan, {}).get("price_id")
            if not price_id:
                self.error_message = f"Invalid plan '{plan}' selected."
                self.is_loading = False
                return
            stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
            checkout_session = stripe.checkout.Session.create(
                line_items=[{"price": price_id, "quantity": 1}],
                mode="subscription",
                success_url="http://localhost:3000/?session_id={CHECKOUT_SESSION_ID}",
                cancel_url="http://localhost:3000/billing",
                customer_email=auth_state.email,
                metadata={"user_id": auth_state.user_id},
            )
            if checkout_session.url:
                self.is_loading = False
                return rx.redirect(checkout_session.url)
            else:
                self.error_message = (
                    "Could not create a checkout session. Please try again."
                )
        except Exception as e:
            logging.exception(f"Error creating Stripe checkout session: {e}")
            self.error_message = "An unexpected error occurred. Please contact support."
        finally:
            self.is_loading = False

    @rx.event
    async def create_customer_portal_session(self):
        """Create a Stripe Customer Portal session to manage subscriptions."""
        self.is_loading = True
        try:
            app_state = await self.get_state(AppState)
            org_id = app_state.active_organization_id
            if not org_id:
                self.error_message = "No active organization found."
                return
            portal_url = "https://billing.stripe.com/p/login/test_7sI5lQ0Z2d4J4VO9AA"
            return rx.redirect(portal_url)
        except Exception as e:
            logging.exception(f"Error creating customer portal session: {e}")
            self.error_message = "Could not open billing management."
        finally:
            self.is_loading = False