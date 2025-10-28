import reflex as rx
from app.state import AppState
from app.components.upgrade_prompts import usage_meter

TECH_STACK_LIMITS = {"free": 5, "pro": 50, "enterprise": 10000}


def tech_item_badge(item: str) -> rx.Component:
    return rx.el.div(
        rx.el.span(item, class_name="text-sm font-medium"),
        rx.el.button(
            rx.icon("x", class_name="h-3 w-3"),
            on_click=lambda: AppState.remove_tech_item(item),
            class_name="ml-2 p-0.5 rounded-full hover:bg-gray-200",
        ),
        class_name="flex items-center bg-gray-100 text-gray-800 px-3 py-1 rounded-full border border-gray-200",
    )


def tech_stack_page() -> rx.Component:
    """The tech stack page content."""
    current_limit = TECH_STACK_LIMITS.get(AppState.active_org_plan.to(str), 5)
    at_limit = AppState.tech_stack.length() >= current_limit
    return rx.el.div(
        rx.el.h1(
            "My Technology Stack", class_name="text-3xl font-bold text-gray-800 mb-6"
        ),
        usage_meter(
            current=AppState.tech_stack.length(),
            limit=current_limit,
            item_name="Technologies",
            tier_name=AppState.active_org_plan.capitalize(),
        ),
        rx.el.div(
            rx.el.div(
                rx.el.input(
                    placeholder="Enter a new technology",
                    on_change=AppState.set_new_tech_stack_item,
                    class_name="flex-grow p-2 border border-gray-300 rounded-l-lg",
                    default_value=AppState.new_tech_stack_item,
                    is_disabled=at_limit,
                ),
                rx.el.button(
                    "Add Technology",
                    on_click=AppState.add_tech_item,
                    class_name="bg-teal-400 text-white px-4 py-2 rounded-r-lg font-semibold hover:bg-teal-500 transition disabled:opacity-50 disabled:cursor-not-allowed",
                    is_disabled=at_limit,
                ),
                class_name="flex",
            ),
            rx.cond(
                at_limit,
                rx.el.p(
                    "You have reached the tech stack limit for your plan. ",
                    rx.el.a(
                        "Upgrade to add more.",
                        href="/billing",
                        class_name="underline font-semibold text-teal-600",
                    ),
                    class_name="text-sm text-red-600 mt-2",
                ),
                None,
            ),
            class_name="my-6",
        ),
        rx.el.div(
            rx.foreach(AppState.tech_stack, tech_item_badge),
            class_name="flex flex-wrap gap-2",
        ),
        class_name="p-8",
    )