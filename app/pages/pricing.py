import reflex as rx
from app.states.billing_state import BillingState, STRIPE_PLANS
from app.components.tools_layout import tools_layout, tools_header, tools_footer


def feature_item(feature: str) -> rx.Component:
    return rx.el.li(
        rx.icon("check", class_name="text-teal-500 mr-2"),
        rx.el.span(feature, class_name="text-gray-300"),
        class_name="flex items-center",
    )


def pricing_plan_card(plan_key: str, plan_details: dict) -> rx.Component:
    is_pro = plan_key == "pro"
    price_val = plan_details.get("price", "Custom")
    price = rx.cond(
        str(rx.Var.create(price_val)) == "Custom",
        "Custom",
        rx.cond(
            BillingState.show_annual_pricing,
            f"${(rx.Var.create(price_val).to(int) * 12 * 0.8).to(int)}",
            f"${rx.Var.create(price_val).to(int)}",
        ),
    )
    period = rx.cond(
        str(rx.Var.create(price_val)) != "Custom",
        rx.cond(BillingState.show_annual_pricing, "/year", "/month"),
        "",
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
            plan_details["name"], class_name="text-2xl font-bold text-white text-center"
        ),
        rx.el.div(
            rx.el.span(price, class_name="text-5xl font-bold"),
            rx.el.span(period, class_name="text-gray-400"),
            class_name="flex items-baseline justify-center my-6 text-white",
        ),
        rx.el.ul(
            rx.foreach(plan_details["features"], feature_item),
            class_name="space-y-3 mb-8 flex-grow",
        ),
        rx.el.a(
            rx.el.button(
                rx.cond(
                    plan_key == "free",
                    "Get Started",
                    rx.cond(
                        (plan_key == "enterprise") | (plan_key == "white_label"),
                        "Contact Sales",
                        "Sign Up",
                    ),
                ),
                class_name=rx.cond(
                    is_pro,
                    "w-full bg-teal-400 text-white py-3 rounded-lg font-semibold hover:bg-teal-500 transition",
                    "w-full bg-gray-700 text-white py-3 rounded-lg font-semibold hover:bg-gray-600 transition",
                ),
            ),
            href="/register",
        ),
        class_name=rx.cond(
            is_pro,
            "bg-gray-800 p-8 rounded-lg shadow-lg border-2 border-teal-500 flex flex-col relative",
            "bg-gray-800/50 p-8 rounded-lg border border-gray-700 flex flex-col relative",
        ),
    )


def pricing_page() -> rx.Component:
    """Public pricing page for prospective customers."""
    return tools_layout(
        rx.el.div(
            rx.el.h1(
                "Find the plan that's right for you",
                class_name="text-5xl font-bold text-center text-white mt-16",
            ),
            rx.el.p(
                "Simple, transparent pricing for teams of all sizes.",
                class_name="text-xl text-gray-400 text-center mt-4 mb-12",
            ),
            rx.el.div(
                rx.el.button(
                    "Monthly",
                    class_name=rx.cond(
                        ~BillingState.show_annual_pricing,
                        "bg-teal-500 text-white px-4 py-1 rounded-l-lg",
                        "bg-gray-700 text-white px-4 py-1 rounded-l-lg",
                    ),
                    on_click=BillingState.toggle_pricing_period,
                ),
                rx.el.button(
                    "Annually (Save 20%)",
                    class_name=rx.cond(
                        BillingState.show_annual_pricing,
                        "bg-teal-500 text-white px-4 py-1 rounded-r-lg",
                        "bg-gray-700 text-white px-4 py-1 rounded-r-lg",
                    ),
                    on_click=BillingState.toggle_pricing_period,
                ),
                class_name="flex justify-center mb-12",
            ),
            rx.el.div(
                pricing_plan_card("free", STRIPE_PLANS["free"]),
                pricing_plan_card("starter", STRIPE_PLANS["starter"]),
                pricing_plan_card("pro", STRIPE_PLANS["pro"]),
                pricing_plan_card("enterprise", STRIPE_PLANS["enterprise"]),
                class_name="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 max-w-7xl mx-auto",
            ),
            rx.el.div(
                rx.el.h2(
                    "Need a fully-branded solution?",
                    class_name="text-3xl font-bold text-white text-center mt-24",
                ),
                rx.el.div(
                    pricing_plan_card("white_label", STRIPE_PLANS["white_label"]),
                    class_name="max-w-md mx-auto mt-8",
                ),
            ),
            class_name="container mx-auto px-4 md:px-6 py-12",
        )
    )