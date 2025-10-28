import reflex as rx
from app.states.billing_state import BillingState, STRIPE_PLANS
from app.states.upgrade_modal_state import UpgradeModalState


def pro_badge() -> rx.Component:
    """A small 'PRO' badge for premium features."""
    return rx.tooltip(
        rx.el.span(
            "PRO",
            class_name="text-xs font-bold bg-teal-100 text-teal-700 px-2 py-0.5 rounded-md ml-2",
        ),
        label="This feature is available on the Pro plan and above.",
    )


def enterprise_badge() -> rx.Component:
    """A small 'ENTERPRISE' badge for premium features."""
    return rx.tooltip(
        rx.el.span(
            "ENTERPRISE",
            class_name="text-xs font-bold bg-purple-100 text-purple-700 px-2 py-0.5 rounded-md ml-2",
        ),
        label="This feature is available on the Enterprise plan.",
    )


def locked_feature(feature_name: str, required_tier: str) -> rx.Component:
    """A placeholder for a locked feature that triggers the upgrade modal."""
    return rx.el.button(
        rx.icon("lock", class_name="mr-2 h-4 w-4"),
        f"Upgrade to Unlock",
        on_click=lambda: UpgradeModalState.show_upgrade_modal(
            feature_name, required_tier
        ),
        class_name="flex items-center text-sm bg-gray-200 text-gray-600 px-3 py-1.5 rounded-md font-medium hover:bg-gray-300",
    )


def usage_meter(
    current: rx.Var[int], limit: rx.Var[int], item_name: str, tier_name: rx.Var[str]
) -> rx.Component:
    """A progress bar to show resource usage against a tier limit."""
    percentage = current / limit * 100
    return rx.el.div(
        rx.el.div(
            rx.el.p(
                f"{current} / {limit} {item_name} used",
                class_name="text-sm font-medium text-gray-700",
            ),
            rx.el.p(
                f"Your {tier_name} plan includes {limit} {item_name}.",
                class_name="text-xs text-gray-500",
            ),
            class_name="flex justify-between items-baseline mb-1",
        ),
        rx.el.div(
            rx.el.div(
                class_name=rx.cond(
                    percentage >= 90,
                    "bg-red-500",
                    rx.cond(percentage >= 70, "bg-yellow-500", "bg-teal-500"),
                ),
                style={"width": percentage.to_string() + "%"},
            ),
            class_name="w-full bg-gray-200 rounded-full h-2.5",
        ),
        class_name="w-full max-w-sm",
    )


def upgrade_modal() -> rx.Component:
    """A dialog to prompt users to upgrade their plan."""
    stripe_plans_var = rx.Var.create(STRIPE_PLANS)
    return rx.radix.primitives.dialog.root(
        rx.radix.primitives.dialog.content(
            rx.radix.primitives.dialog.title(
                f"Upgrade to {UpgradeModalState.required_tier.capitalize()} to Use {UpgradeModalState.feature_name}",
                class_name="text-2xl font-bold text-gray-800",
            ),
            rx.radix.primitives.dialog.description(
                f"The '{UpgradeModalState.feature_name}' feature is only available on the {UpgradeModalState.required_tier.capitalize()} plan.",
                class_name="text-gray-600 mt-2 mb-6",
            ),
            rx.el.div(
                rx.el.h4(
                    f"The {UpgradeModalState.required_tier.capitalize()} plan includes:",
                    class_name="font-semibold text-gray-700 mb-2",
                ),
                rx.el.ul(
                    rx.foreach(
                        UpgradeModalState.required_tier_features,
                        lambda feature: rx.el.li(
                            rx.icon(
                                "square_check", class_name="h-5 w-5 text-teal-500 mr-2"
                            ),
                            feature,
                            class_name="flex items-center text-gray-600",
                        ),
                    ),
                    class_name="space-y-2 mb-6",
                ),
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.p("Starting at", class_name="text-sm text-gray-500"),
                    rx.el.p(
                        f"${UpgradeModalState.required_tier_price}/month",
                        class_name="text-3xl font-bold text-gray-900",
                    ),
                ),
                rx.el.a(
                    rx.el.button(
                        "Upgrade Now",
                        class_name="w-full bg-teal-500 text-white py-2 rounded-md font-semibold hover:bg-teal-600 transition",
                    ),
                    href="/billing",
                ),
                class_name="flex items-center justify-between p-4 bg-gray-50 rounded-lg",
            ),
            rx.el.div(
                rx.radix.primitives.dialog.close(
                    rx.el.button(
                        rx.icon("x", class_name="h-5 w-5"),
                        class_name="absolute top-3 right-3 p-1 rounded-full text-gray-500 hover:bg-gray-100",
                    )
                ),
                class_name="flex justify-end gap-4 mt-4",
            ),
        ),
        open=UpgradeModalState.is_open,
        on_open_change=UpgradeModalState.close_upgrade_modal,
    )