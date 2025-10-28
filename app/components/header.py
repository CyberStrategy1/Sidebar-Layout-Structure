import reflex as rx
from app.state import AppState
from app.states.auth_state import AuthState


def user_profile_menu() -> rx.Component:
    return rx.el.div(
        rx.el.button(
            rx.el.div(
                rx.el.span(
                    AppState.user_profile["full_name"], class_name="font-semibold"
                ),
                rx.icon("chevron-down", class_name="h-4 w-4"),
                class_name="flex items-center gap-2",
            ),
            class_name="flex items-center text-sm font-medium text-gray-700 hover:text-gray-900",
        )
    )


def organization_switcher() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("building", class_name="h-5 w-5 text-gray-500"),
            rx.el.select(
                rx.foreach(
                    AppState.memberships,
                    lambda membership: rx.el.option(
                        membership["organization"]["name"],
                        value=membership["organization"]["id"],
                    ),
                ),
                value=AppState.active_organization_id,
                on_change=AppState.switch_organization,
                class_name="-ml-1 bg-transparent border-none focus:ring-0 text-sm font-medium text-gray-700",
                variant="soft",
            ),
            class_name="flex items-center gap-2",
        ),
        class_name="flex items-center",
    )


def header() -> rx.Component:
    """The application header component."""
    return rx.el.header(
        rx.el.div(
            organization_switcher(),
            user_profile_menu(),
            class_name="flex h-16 items-center justify-between px-6",
        ),
        class_name="sticky top-0 z-10 border-b bg-white/80 backdrop-blur-sm",
    )