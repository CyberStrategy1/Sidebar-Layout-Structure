import reflex as rx
from app.states.api_state import ApiState
from app.components.upgrade_prompts import enterprise_badge, locked_feature
from app.state import AppState
from app.models import ApiKey


def api_key_row(api_key: ApiKey) -> rx.Component:
    return rx.el.tr(
        rx.el.td(api_key["key_name"], class_name="px-6 py-4 font-medium text-gray-900"),
        rx.el.td(
            rx.el.div(
                rx.el.input(
                    is_read_only=True,
                    class_name="font-mono text-sm border-none bg-transparent p-0",
                    default_value=api_key["masked_key"],
                    key=api_key["masked_key"],
                ),
                rx.el.button(
                    rx.icon("copy", class_name="h-4 w-4"),
                    on_click=rx.set_clipboard(api_key["full_key"]),
                    class_name="text-gray-500 hover:text-gray-900",
                ),
                class_name="flex items-center gap-2",
            ),
            class_name="px-6 py-4",
        ),
        rx.el.td("Full Access", class_name="px-6 py-4 text-sm text-gray-500"),
        rx.el.td(
            api_key["created_at"].to(str).split("T")[0],
            class_name="px-6 py-4 text-sm text-gray-500",
        ),
        rx.el.td(
            rx.el.button(
                "Revoke",
                on_click=lambda: ApiState.revoke_api_key(api_key["id"]),
                class_name="text-red-600 hover:text-red-900 font-semibold text-sm",
                is_loading=ApiState.is_loading
                & (ApiState.revoking_key_id == api_key["id"]),
            ),
            class_name="px-6 py-4 text-right",
        ),
    )


def api_config_page() -> rx.Component:
    """The API configuration page content."""
    return rx.el.div(
        rx.el.h1(
            "API Configuration", class_name="text-3xl font-bold text-gray-800 mb-6"
        ),
        rx.cond(
            AppState.can_use_api_access,
            rx.el.div(
                rx.el.div(
                    rx.el.div(
                        rx.el.h2("Manage API Keys", class_name="text-xl font-bold"),
                        rx.el.p(
                            "Create and revoke API keys for programmatic access.",
                            class_name="text-sm text-gray-500",
                        ),
                    ),
                    rx.el.form(
                        rx.el.input(
                            name="key_name",
                            placeholder="e.g., 'CI/CD Pipeline Key'",
                            class_name="border rounded-l-md p-2 text-sm w-72",
                        ),
                        rx.el.button(
                            "Generate New Key",
                            type="submit",
                            class_name="bg-teal-500 text-white px-4 py-2 rounded-r-md font-semibold hover:bg-teal-600",
                            is_loading=ApiState.is_loading,
                        ),
                        on_submit=ApiState.generate_api_key,
                        class_name="flex",
                    ),
                    class_name="flex justify-between items-center mb-6",
                ),
                rx.el.div(
                    rx.el.table(
                        rx.el.thead(
                            rx.el.tr(
                                rx.el.th(
                                    "Name",
                                    class_name="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase",
                                ),
                                rx.el.th(
                                    "Key",
                                    class_name="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase",
                                ),
                                rx.el.th(
                                    "Permissions",
                                    class_name="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase",
                                ),
                                rx.el.th(
                                    "Created",
                                    class_name="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase",
                                ),
                                rx.el.th("", class_name="relative px-6 py-3"),
                            )
                        ),
                        rx.el.tbody(rx.foreach(ApiState.api_keys, api_key_row)),
                        class_name="min-w-full divide-y divide-gray-200",
                    ),
                    class_name="bg-white rounded-lg shadow-sm border overflow-hidden",
                ),
                rx.el.div(
                    rx.el.h2(
                        "API Documentation", class_name="text-xl font-bold mt-12 mb-4"
                    ),
                    rx.el.div(
                        rx.el.code(
                            "GET /api/v1/health",
                            class_name="font-mono text-sm bg-gray-100 p-4 rounded-md block mb-4",
                        ),
                        rx.el.code(
                            "GET /api/v1/vulnerabilities",
                            class_name="font-mono text-sm bg-gray-100 p-4 rounded-md block",
                        ),
                        class_name="bg-white p-6 rounded-lg shadow-sm border",
                    ),
                ),
            ),
            locked_feature(feature_name="API Access", required_tier="enterprise"),
        ),
        class_name="p-8",
        on_mount=ApiState.load_api_keys,
    )