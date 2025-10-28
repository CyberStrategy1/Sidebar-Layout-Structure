import reflex as rx
from app.state import AppState


def analysis_page() -> rx.Component:
    """The CVE analysis page content."""
    return rx.el.div(
        rx.el.div(
            rx.el.h1(
                "CVE Enrichment Analysis", class_name="text-3xl font-bold text-gray-800"
            ),
            rx.el.button(
                "Fetch Recent CVEs (Last 30 Days)",
                on_click=AppState.fetch_recent_modified_cves,
                is_loading=AppState.is_loading,
                class_name="bg-teal-400 text-white px-4 py-2 rounded-lg font-semibold hover:bg-teal-500 transition",
            ),
            class_name="flex justify-between items-center mb-6",
        ),
        rx.el.div(
            rx.data_table(
                data=AppState.enrichment_analysis_results,
                columns=[
                    {"title": "CVE ID", "type": "str"},
                    {"title": "Enrichment Lag (Days)", "type": "int"},
                ],
                pagination=True,
                search=True,
                sort=True,
                resizable=True,
                default_sort=[("Enrichment Lag (Days)", "desc")],
            ),
            class_name="mt-8",
        ),
        class_name="p-8",
    )