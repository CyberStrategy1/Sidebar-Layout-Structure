import reflex as rx
from app.states.billing_state import BillingState, STRIPE_PLANS
from app.states.auth_state import AuthState
from app.state import AppState


def feature_item(feature: str) -> rx.Component:
    return rx.el.li(
        rx.icon("check", class_name="text-teal-500 mr-2"),
        rx.el.span(feature, class_name="text-gray-600"),
        class_name="flex items-center",
    )


def plan_card(plan_key: str, plan_details: dict) -> rx.Component:
    is_current_plan = AppState.active_org_plan == plan_key
    is_pro = plan_key == "pro"
    price_val = rx.Var.create(plan_details.get("price", 0))
    price = rx.cond(
        str(price_val) == "Custom",
        "Custom",
        rx.cond(
            price_val.to(int) > 0,
            rx.cond(
                BillingState.show_annual_pricing,
                f"${(price_val.to(int) * 12 * 0.8).to(int)}/year",
                f"${str(price_val)}/month",
            ),
            "Free",
        ),
    )
    return rx.el.div(
        rx.cond(
            is_pro,
            rx.el.div(
                "Most Popular",
                class_name="absolute -top-3.5 left-1/2 -translate-x-1/2 bg-teal-500 text-white text-xs font-bold px-3 py-1 rounded-full",
            ),
            None,
        ),
        rx.el.h3(
            plan_details["name"],
            class_name="text-2xl font-bold text-gray-800 text-center",
        ),
        rx.el.p(price, class_name="text-4xl font-bold my-4 text-center"),
        rx.el.ul(
            rx.foreach(plan_details["features"], feature_item),
            class_name="space-y-2 mb-6 flex-grow",
        ),
        rx.cond(
            is_current_plan,
            rx.el.button(
                "Current Plan",
                is_disabled=True,
                class_name="w-full bg-gray-200 text-gray-500 py-2 rounded-md font-semibold cursor-not-allowed",
            ),
            rx.cond(
                (plan_key == "enterprise") | (plan_key == "white_label"),
                rx.el.button(
                    "Contact Sales",
                    class_name="w-full bg-purple-500 text-white py-2 rounded-md font-semibold hover:bg-purple-600 transition",
                ),
                rx.el.button(
                    "Subscribe",
                    on_click=lambda: BillingState.create_checkout_session(plan_key),
                    is_loading=BillingState.is_loading
                    & (BillingState.selected_plan == plan_key),
                    class_name="w-full bg-teal-400 text-white py-2 rounded-md font-semibold hover:bg-teal-500 transition disabled:opacity-50",
                ),
            ),
        ),
        class_name=rx.cond(
            is_current_plan,
            "bg-white p-8 rounded-lg shadow-lg border-2 border-teal-500 flex flex-col relative",
            "bg-white p-8 rounded-lg shadow-sm border border-gray-200 flex flex-col relative",
        ),
    )


def billing_page() -> rx.Component:
    """The billing page for managing subscriptions."""
    return rx.el.div(
        rx.el.div(
            rx.el.h1(
                "Billing & Subscriptions", class_name="text-3xl font-bold text-gray-800"
            ),
            rx.el.p(
                "Manage your plan and billing details.", class_name="text-gray-600 mt-1"
            ),
            class_name="mb-8",
        ),
        rx.el.div(
            rx.el.h2(
                "Current Plan", class_name="text-xl font-semibold text-gray-700 mb-4"
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.p(
                        f"Your Plan: {AppState.active_org_plan.capitalize()}",
                        class_name="font-bold text-lg",
                    ),
                    rx.el.p(
                        f"Manage your subscription and payment methods via our secure portal.",
                        class_name="text-sm text-gray-500",
                    ),
                ),
                rx.el.button(
                    "Manage Billing",
                    on_click=BillingState.create_customer_portal_session,
                    is_loading=BillingState.is_loading,
                    class_name="bg-gray-200 text-gray-700 px-4 py-2 rounded-md font-semibold hover:bg-gray-300",
                ),
                class_name="flex justify-between items-center bg-white p-6 rounded-lg shadow-sm border border-gray-200 mb-8",
            ),
            rx.el.h2(
                "Choose Your Plan",
                class_name="text-2xl font-bold text-gray-800 mb-4 text-center",
            ),
            rx.el.div(
                rx.el.button(
                    "Monthly",
                    class_name=rx.cond(
                        ~BillingState.show_annual_pricing,
                        "bg-teal-500 text-white px-4 py-1 rounded-l-lg",
                        "bg-gray-200 px-4 py-1 rounded-l-lg",
                    ),
                    on_click=BillingState.toggle_pricing_period,
                ),
                rx.el.button(
                    "Annually (Save 20%)",
                    class_name=rx.cond(
                        BillingState.show_annual_pricing,
                        "bg-teal-500 text-white px-4 py-1 rounded-r-lg",
                        "bg-gray-200 px-4 py-1 rounded-r-lg",
                    ),
                    on_click=BillingState.toggle_pricing_period,
                ),
                class_name="flex justify-center mb-8",
            ),
            rx.el.div(
                plan_card("free", STRIPE_PLANS["free"]),
                plan_card("starter", STRIPE_PLANS["starter"]),
                plan_card("pro", STRIPE_PLANS["pro"]),
                plan_card("enterprise", STRIPE_PLANS["enterprise"]),
                class_name="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-7xl mx-auto",
            ),
            rx.el.div(
                rx.el.h2(
                    "White Label Solution",
                    class_name="text-2xl font-bold text-gray-800 mt-16 mb-4 text-center",
                ),
                plan_card("white_label", STRIPE_PLANS["white_label"]),
                class_name="max-w-md mx-auto",
            ),
            rx.cond(
                BillingState.error_message != "",
                rx.el.div(
                    BillingState.error_message,
                    class_name="mt-4 text-center text-sm text-red-600 p-3 bg-red-50 border border-red-200 rounded-md",
                ),
                None,
            ),
        ),
        class_name="p-8",
    )