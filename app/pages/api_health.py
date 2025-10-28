import reflex as rx
from app.states.admin_state import AdminState


def status_badge(status: str) -> rx.Component:
    """A badge to display the status of an API call."""
    return rx.el.span(
        status,
        class_name=rx.cond(
            status == "success",
            "bg-green-100 text-green-800 text-xs font-medium px-2.5 py-0.5 rounded-full w-fit",
            "bg-red-100 text-red-800 text-xs font-medium px-2.5 py-0.5 rounded-full w-fit",
        ),
    )


def diagnostic_panel(log_id: str, advice: str) -> rx.Component:
    """A panel to display AI diagnostic advice."""
    return rx.el.div(
        rx.el.h4(
            "AI Diagnostic Advice", class_name="font-bold text-md text-gray-700 mb-2"
        ),
        rx.markdown(advice),
        class_name="bg-gray-100 p-4 mt-2 border-l-4 border-teal-400",
    )


def log_row(log: dict) -> rx.Component:
    """A row in the API health log table."""
    log_id = log["id"].to_string()
    status_code_str = log["status_code"].to_string()
    duration_str = log["duration_ms"].to_string()
    return rx.fragment(
        rx.el.tr(
            rx.el.td(log["api_name"], class_name="px-4 py-3"),
            rx.el.td(log["endpoint"], class_name="px-4 py-3 truncate max-w-xs"),
            rx.el.td(status_badge(log["status"]), class_name="px-4 py-3"),
            rx.el.td(status_code_str, class_name="px-4 py-3"),
            rx.el.td(f"{duration_str} ms", class_name="px-4 py-3"),
            rx.el.td(log["start_time"], class_name="px-4 py-3"),
            rx.el.td(
                rx.cond(
                    log["status"] == "failure",
                    rx.el.button(
                        rx.icon("sparkles", class_name="mr-1 h-4 w-4"),
                        "Diagnose with AI",
                        on_click=lambda: AdminState.diagnose_with_ai(
                            log["id"], log["api_name"], log["error_message"]
                        ),
                        is_loading=AdminState.is_diagnosing
                        & (AdminState.selected_log_id == log_id),
                        class_name="bg-yellow-400 text-yellow-900 px-3 py-1 rounded-md text-xs font-semibold hover:bg-yellow-500 transition flex items-center",
                    ),
                    rx.el.span("-", class_name="text-gray-500"),
                ),
                class_name="px-4 py-3",
            ),
            class_name="border-b border-gray-200 bg-white hover:bg-gray-50",
        ),
        rx.cond(
            AdminState.diagnostic_result.contains(log_id),
            rx.el.tr(
                rx.el.td(
                    diagnostic_panel(log_id, AdminState.diagnostic_result[log_id]),
                    col_span=7,
                    class_name="p-0 bg-gray-50",
                )
            ),
            None,
        ),
    )


def api_health_page() -> rx.Component:
    """The API Health Monitoring page content."""
    return rx.el.div(
        rx.el.div(
            rx.el.h1(
                "API Health Monitor", class_name="text-3xl font-bold text-gray-800"
            ),
            rx.el.button(
                "Refresh Data",
                on_click=AdminState.fetch_api_health_logs,
                is_loading=AdminState.is_loading,
                class_name="bg-teal-400 text-white px-4 py-2 rounded-lg font-semibold hover:bg-teal-500 transition",
            ),
            class_name="flex justify-between items-center mb-6",
        ),
        rx.cond(
            AdminState.is_loading & (AdminState.api_health_logs.length() == 0),
            rx.el.div(
                rx.spinner(class_name="h-12 w-12 text-teal-500"),
                class_name="flex justify-center items-center h-96",
            ),
            rx.el.div(
                rx.el.table(
                    rx.el.thead(
                        rx.el.tr(
                            rx.el.th(
                                "API Name",
                                class_name="text-left px-4 py-3 font-semibold text-gray-600 bg-gray-50",
                            ),
                            rx.el.th(
                                "Endpoint",
                                class_name="text-left px-4 py-3 font-semibold text-gray-600 bg-gray-50",
                            ),
                            rx.el.th(
                                "Status",
                                class_name="text-left px-4 py-3 font-semibold text-gray-600 bg-gray-50",
                            ),
                            rx.el.th(
                                "Status Code",
                                class_name="text-left px-4 py-3 font-semibold text-gray-600 bg-gray-50",
                            ),
                            rx.el.th(
                                "Duration",
                                class_name="text-left px-4 py-3 font-semibold text-gray-600 bg-gray-50",
                            ),
                            rx.el.th(
                                "Timestamp",
                                class_name="text-left px-4 py-3 font-semibold text-gray-600 bg-gray-50",
                            ),
                            rx.el.th(
                                "Actions",
                                class_name="text-left px-4 py-3 font-semibold text-gray-600 bg-gray-50",
                            ),
                        )
                    ),
                    rx.el.tbody(rx.foreach(AdminState.api_health_logs, log_row)),
                    class_name="w-full text-sm text-gray-700",
                ),
                class_name="overflow-x-auto rounded-lg border border-gray-200 shadow-sm",
            ),
        ),
        class_name="p-8",
        on_mount=AdminState.fetch_api_health_logs,
    )