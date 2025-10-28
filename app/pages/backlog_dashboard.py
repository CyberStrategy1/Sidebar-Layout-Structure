import reflex as rx
from app.states.backlog_state import BacklogState


def backlog_dashboard_page() -> rx.Component:
    """The CVE Backlog Dashboard page."""
    return rx.el.div(
        rx.el.div(
            rx.el.h1(
                "NVD CVE Backlog Dashboard",
                class_name="text-3xl font-bold text-gray-800",
            ),
            rx.el.p(
                "Monitoring CVEs currently 'Awaiting Analysis' by NIST.",
                class_name="text-gray-600 mt-1",
            ),
            class_name="mb-6",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    "Total CVEs Awaiting Analysis",
                    class_name="text-sm font-medium text-gray-500",
                ),
                rx.el.p(
                    BacklogState.total_backlog_count.to_string(),
                    class_name="text-4xl font-bold text-red-600 mt-2",
                ),
                class_name="bg-white p-6 rounded-lg shadow-sm border border-gray-200",
            ),
            class_name="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8",
        ),
        rx.el.div(
            rx.el.h2(
                "Backlog by Month", class_name="text-xl font-bold text-gray-800 mb-4"
            ),
            rx.el.table(
                rx.el.thead(
                    rx.el.tr(
                        rx.el.th("Month", class_name="px-4 py-2 text-left"),
                        rx.el.th("CVE Count", class_name="px-4 py-2 text-left"),
                        rx.el.th(
                            "Average Days Waiting", class_name="px-4 py-2 text-left"
                        ),
                    )
                ),
                rx.el.tbody(
                    rx.foreach(
                        BacklogState.backlog_by_month,
                        lambda item: rx.el.tr(
                            rx.el.td(item["month"], class_name="px-4 py-2"),
                            rx.el.td(item["count"], class_name="px-4 py-2"),
                            rx.el.td(item["avg_days_waiting"], class_name="px-4 py-2"),
                            class_name="border-b",
                        ),
                    )
                ),
                class_name="w-full text-sm",
            ),
            class_name="bg-white p-6 rounded-lg shadow-sm border border-gray-200",
        ),
        class_name="p-8",
        on_mount=BacklogState.fetch_backlog_data,
    )