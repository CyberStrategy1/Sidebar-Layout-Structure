import reflex as rx
from app.states.reporting_state import ReportingState
from app.components.upgrade_prompts import enterprise_badge, pro_badge, locked_feature
from app.state import AppState


def create_report_dialog() -> rx.Component:
    return rx.radix.primitives.dialog.root(
        rx.radix.primitives.dialog.trigger(
            rx.el.button(
                rx.icon("plus", class_name="mr-2 h-4 w-4"),
                "Create Report",
                enterprise_badge(),
                on_click=lambda: ReportingState.set_show_create_dialog(True),
                class_name="bg-teal-400 text-white px-4 py-2 rounded-lg font-semibold hover:bg-teal-500 transition flex items-center",
            )
        ),
        rx.radix.primitives.dialog.content(
            rx.radix.primitives.dialog.title(
                "Create New Report", class_name="text-lg font-bold"
            ),
            rx.radix.primitives.dialog.description(
                "Enter the details for your new report.",
                class_name="text-sm text-gray-500 mb-4",
            ),
            rx.el.form(
                rx.el.div(
                    rx.el.label("Report Name", class_name="text-sm font-medium"),
                    rx.el.input(
                        name="name",
                        placeholder="Q3 Vulnerability Summary",
                        class_name="w-full p-2 mt-1 border rounded-md",
                    ),
                    class_name="mb-4",
                ),
                rx.el.div(
                    rx.el.label("Description", class_name="text-sm font-medium"),
                    rx.el.textarea(
                        name="description",
                        placeholder="A summary of all critical vulnerabilities found in Q3.",
                        class_name="w-full p-2 mt-1 border rounded-md",
                    ),
                    class_name="mb-4",
                ),
                rx.el.div(
                    rx.radix.primitives.dialog.close(
                        rx.el.button(
                            "Cancel",
                            class_name="bg-gray-200 text-gray-700 px-4 py-2 rounded-md font-semibold hover:bg-gray-300",
                            type="button",
                            on_click=lambda: ReportingState.set_show_create_dialog(
                                False
                            ),
                        )
                    ),
                    rx.el.button(
                        "Create",
                        type="submit",
                        is_loading=ReportingState.is_loading,
                        class_name="bg-teal-500 text-white px-4 py-2 rounded-md font-semibold hover:bg-teal-600",
                    ),
                    class_name="flex justify-end gap-4 mt-4",
                ),
                on_submit=ReportingState.create_report,
            ),
        ),
        open=ReportingState.show_create_dialog,
        on_open_change=ReportingState.set_show_create_dialog,
    )


def report_row(report: dict) -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            rx.el.div(report["name"], class_name="font-medium text-gray-900"),
            rx.el.div(report["description"], class_name="text-sm text-gray-500"),
            class_name="px-6 py-4 whitespace-nowrap",
        ),
        rx.el.td(
            rx.el.span(
                report["report_type"].to_string().capitalize(),
                class_name="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800",
            ),
            class_name="px-6 py-4 whitespace-nowrap",
        ),
        rx.el.td(
            report["created_at"].to_string().split("T")[0],
            class_name="px-6 py-4 whitespace-nowrap text-sm text-gray-500",
        ),
        rx.el.td(
            "Admin", class_name="px-6 py-4 whitespace-nowrap text-sm text-gray-500"
        ),
        rx.el.td(
            rx.el.div(
                rx.cond(
                    AppState.can_export_pdf,
                    rx.el.button(
                        "Export PDF",
                        class_name="text-teal-600 hover:text-teal-900 font-semibold text-sm mr-4",
                    ),
                    locked_feature(feature_name="PDF Export", required_tier="pro"),
                ),
                rx.el.button(
                    "View Details",
                    class_name="text-gray-600 hover:text-gray-900 font-semibold text-sm",
                ),
                class_name="flex items-center justify-end",
            ),
            class_name="px-6 py-4 whitespace-nowrap text-right text-sm font-medium",
        ),
        class_name="bg-white divide-y divide-gray-200",
    )


def empty_state() -> rx.Component:
    return rx.el.div(
        rx.icon("file-text", class_name="mx-auto h-12 w-12 text-gray-400"),
        rx.el.h3(
            "No reports found", class_name="mt-2 text-sm font-medium text-gray-900"
        ),
        rx.el.p(
            "Get started by creating a new report.",
            class_name="mt-1 text-sm text-gray-500",
        ),
        rx.el.div(create_report_dialog(), class_name="mt-6"),
        class_name="text-center py-16",
    )


def statistic_card(title: str, value: rx.Var[str | int]) -> rx.Component:
    return rx.el.div(
        rx.el.dt(title, class_name="text-sm font-medium text-gray-500 truncate"),
        rx.el.dd(
            value.to_string(), class_name="mt-1 text-3xl font-semibold text-gray-900"
        ),
        class_name="px-4 py-5 bg-white shadow rounded-lg overflow-hidden sm:p-6",
    )


def reporting_page() -> rx.Component:
    """The reporting page content."""
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.h1(
                    "Reporting Dashboard", class_name="text-3xl font-bold text-gray-800"
                ),
                rx.el.p(
                    "Create, manage, and export vulnerability reports.",
                    class_name="text-gray-600 mt-1",
                ),
            ),
            create_report_dialog(),
            class_name="flex justify-between items-start mb-8",
        ),
        rx.el.dl(
            statistic_card("Total Reports", ReportingState.total_reports_count),
            statistic_card("Recent Exports (24h)", ReportingState.recent_exports_count),
            rx.el.div(
                rx.el.dt(
                    rx.el.div(
                        "Slack Integration",
                        enterprise_badge(),
                        class_name="flex items-center text-sm font-medium text-gray-500 truncate",
                    )
                ),
                rx.el.dd(
                    rx.cond(
                        AppState.can_use_api_access,
                        rx.el.span(
                            "Enabled",
                            class_name="mt-1 text-3xl font-semibold text-green-600",
                        ),
                        rx.el.span(
                            "Locked",
                            class_name="mt-1 text-3xl font-semibold text-gray-400",
                        ),
                    )
                ),
                class_name="px-4 py-5 bg-white shadow rounded-lg overflow-hidden sm:p-6",
            ),
            rx.el.div(
                rx.el.dt(
                    rx.el.div(
                        "Jira Integration",
                        enterprise_badge(),
                        class_name="flex items-center text-sm font-medium text-gray-500 truncate",
                    )
                ),
                rx.el.dd(
                    rx.cond(
                        AppState.can_use_api_access,
                        rx.el.span(
                            "Enabled",
                            class_name="mt-1 text-3xl font-semibold text-green-600",
                        ),
                        rx.el.span(
                            "Locked",
                            class_name="mt-1 text-3xl font-semibold text-gray-400",
                        ),
                    )
                ),
                class_name="px-4 py-5 bg-white shadow rounded-lg overflow-hidden sm:p-6",
            ),
            class_name="mt-5 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-8",
        ),
        rx.cond(
            ReportingState.is_loading & (ReportingState.reports.length() == 0),
            rx.el.div(
                rx.spinner(class_name="h-12 w-12 text-teal-500"),
                class_name="flex justify-center items-center h-64",
            ),
            rx.cond(
                ReportingState.reports.length() == 0,
                empty_state(),
                rx.el.div(
                    rx.el.div(
                        rx.el.table(
                            rx.el.thead(
                                rx.el.tr(
                                    rx.el.th(
                                        "Report Name",
                                        scope="col",
                                        class_name="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider",
                                    ),
                                    rx.el.th(
                                        "Type",
                                        scope="col",
                                        class_name="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider",
                                    ),
                                    rx.el.th(
                                        "Created",
                                        scope="col",
                                        class_name="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider",
                                    ),
                                    rx.el.th(
                                        "Creator",
                                        scope="col",
                                        class_name="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider",
                                    ),
                                    rx.el.th(
                                        rx.el.span("Actions", class_name="sr-only"),
                                        scope="col",
                                        class_name="relative px-6 py-3",
                                    ),
                                )
                            ),
                            rx.el.tbody(
                                rx.foreach(ReportingState.reports, report_row),
                                class_name="bg-white divide-y divide-gray-200",
                            ),
                            class_name="min-w-full divide-y divide-gray-200",
                        ),
                        class_name="-my-2 overflow-x-auto sm:-mx-6 lg:-mx-8",
                    ),
                    class_name="flex flex-col",
                ),
            ),
        ),
        class_name="p-8",
        on_mount=ReportingState.fetch_reports,
    )