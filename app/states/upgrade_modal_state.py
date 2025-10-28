import reflex as rx
from typing import Literal
from app.states.billing_state import STRIPE_PLANS


class UpgradeModalState(rx.State):
    """State to manage the upgrade modal's visibility and context."""

    is_open: bool = False
    feature_name: str = ""
    required_tier: Literal["pro", "enterprise"] = "pro"

    @rx.var
    def required_tier_price(self) -> int:
        """Get the price for the required tier."""
        plan_details = STRIPE_PLANS.get(self.required_tier, {})
        return int(plan_details.get("price", 0))

    @rx.var
    def required_tier_features(self) -> list[str]:
        """Get the features for the required tier."""
        plan_details = STRIPE_PLANS.get(self.required_tier, {})
        return plan_details.get("features", [])

    @rx.event
    def show_upgrade_modal(
        self, feature_name: str, required_tier: Literal["pro", "enterprise"]
    ):
        """Show the upgrade modal with specific feature context."""
        self.feature_name = feature_name
        self.required_tier = required_tier
        self.is_open = True

    @rx.event
    def close_upgrade_modal(self):
        """Close the upgrade modal."""
        self.is_open = False