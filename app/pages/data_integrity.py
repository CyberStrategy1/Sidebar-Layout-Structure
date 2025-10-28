import reflex as rx
from app.states.data_integrity_state import DataIntegrityState


def status_cell(status: str) -> rx.Component:
    return rx.el.div(
        rx.el.span(
            status,
            class_name=rx.cond(
                status == "Passed",
                "bg-green-100 text-green-800 text-xs font-medium px-2.5 py-1 rounded-full",
                rx.cond(
                    status == "Warning",
                    "bg-yellow-100 text-yellow-800 text-xs font-medium px-2.5 py-1 rounded-full",
                    "bg-red-100 text-red-800 text-xs font-medium px-2.5 py-1 rounded-full",
                ),
            ),
        ),
        class_name="flex items-center justify-center",
    )


def result_row(result: dict) -> rx.Component:
    return rx.el.tr(
        rx.el.td(result["check"], class_name="px-6 py-4 font-medium text-gray-900"),
        rx.el.td(status_cell(result["status"]), class_name="px-6 py-4"),
        rx.el.td(result["details"], class_name="px-6 py-4 text-sm text-gray-600"),
        class_name="border-b hover:bg-gray-50",
    )


def data_integrity_page() -> rx.Component:
    """The Data Integrity Dashboard page."""
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.h1(
                    "Data Integrity Dashboard",
                    class_name="text-3xl font-bold text-gray-800",
                ),
                rx.el.p(
                    "Monitor and validate the consistency of your vulnerability data.",
                    class_name="text-gray-600 mt-1",
                ),
            ),
            rx.el.div(
                rx.el.p(
                    f"Last Scan: {DataIntegrityState.last_scan_time}",
                    class_name="text-sm text-gray-500",
                ),
                rx.el.button(
                    "Run Scan",
                    on_click=DataIntegrityState.run_integrity_scan,
                    is_loading=DataIntegrityState.is_scanning,
                    class_name="bg-teal-400 text-white px-4 py-2 rounded-lg font-semibold hover:bg-teal-500 transition disabled:opacity-50",
                ),
                class_name="flex items-center gap-4",
            ),
            class_name="flex justify-between items-center mb-8",
        ),
        rx.cond(
            DataIntegrityState.is_scanning
            & (DataIntegrityState.scan_results.length() == 0),
            rx.el.div(
                rx.spinner(class_name="h-12 w-12 text-teal-500"),
                rx.el.p("Scanning data sources...", class_name="mt-4 text-gray-600"),
                class_name="flex flex-col items-center justify-center h-96 border rounded-lg bg-gray-50",
            ),
            rx.cond(
                DataIntegrityState.scan_results.length() == 0,
                rx.el.div(
                    rx.icon(
                        "shield-check", class_name="mx-auto h-16 w-16 text-gray-400"
                    ),
                    rx.el.h3(
                        "No scan results yet",
                        class_name="mt-4 text-lg font-medium text-gray-900",
                    ),
                    rx.el.p(
                        "Run a scan to check your data integrity.",
                        class_name="mt-1 text-sm text-gray-500",
                    ),
                    class_name="text-center py-24 border-2 border-dashed rounded-lg",
                ),
                rx.el.div(
                    rx.el.table(
                        rx.el.thead(
                            rx.el.tr(
                                rx.el.th(
                                    "Check Description",
                                    class_name="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider",
                                ),
                                rx.el.th(
                                    "Status",
                                    class_name="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider",
                                ),
                                rx.el.th(
                                    "Details",
                                    class_name="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider",
                                ),
                            )
                        ),
                        rx.el.tbody(
                            rx.foreach(DataIntegrityState.scan_results, result_row)
                        ),
                        class_name="min-w-full divide-y divide-gray-200",
                    ),
                    class_name="overflow-hidden border rounded-lg shadow-sm",
                ),
            ),
        ),
        class_name="p-8",
    )