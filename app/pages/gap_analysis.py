import reflex as rx
from app.states.gap_analysis_state import GapAnalysisState


def metric_card(
    title: str, value: rx.Var[str | int], trend: str, tooltip: str
) -> rx.Component:
    return rx.tooltip(
        rx.el.div(
            rx.el.div(
                rx.el.p(title, class_name="text-sm font-medium text-gray-500"),
                rx.icon("info", class_name="h-4 w-4 text-gray-400"),
                class_name="flex items-center justify-between",
            ),
            rx.el.div(
                rx.el.p(
                    value.to_string(),
                    class_name="text-4xl font-bold text-gray-900 mt-2",
                ),
                rx.el.div(
                    rx.icon("arrow-up-right", class_name="h-4 w-4 text-green-600"),
                    rx.el.span(
                        trend, class_name="text-sm font-semibold text-green-600"
                    ),
                    class_name="flex items-center gap-1",
                ),
                class_name="flex items-baseline justify-between",
            ),
            class_name="bg-white p-6 rounded-lg shadow-sm border border-gray-200",
        ),
        label=tooltip,
    )


def filter_panel() -> rx.Component:
    time_gap_options = [
        ("0-7", "0-7 days"),
        ("7-30", "7-30 days"),
        ("30-90", "30-90 days"),
        ("90-9999", "90+ days"),
    ]
    return rx.el.div(
        rx.el.div(
            rx.el.h3("Filters", class_name="text-lg font-semibold text-gray-800"),
            rx.el.button(
                rx.icon("x", class_name="h-5 w-5"),
                on_click=GapAnalysisState.toggle_filter_panel,
                class_name="p-1 rounded-full hover:bg-gray-200",
            ),
            class_name="flex items-center justify-between p-4 border-b",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.label(
                    "Keyword Search",
                    class_name="text-sm font-medium text-gray-700 mb-1",
                ),
                rx.el.input(
                    placeholder="CVE ID, vendor...",
                    on_change=GapAnalysisState.set_search_term,
                    default_value=GapAnalysisState.filters["search_term"],
                    class_name="w-full p-2 border rounded-md text-sm",
                ),
                class_name="mb-4",
            ),
            rx.el.div(
                rx.el.label(
                    "Time Gap Ranges",
                    class_name="text-sm font-medium text-gray-700 mb-2",
                ),
                rx.el.div(
                    rx.foreach(
                        time_gap_options,
                        lambda option: rx.el.button(
                            option[1],
                            on_click=lambda: GapAnalysisState.toggle_time_gap_filter(
                                option[0]
                            ),
                            class_name=rx.cond(
                                GapAnalysisState.filters["time_gap_ranges"].contains(
                                    option[0]
                                ),
                                "w-full text-left p-2 rounded-md text-sm bg-blue-100 text-blue-800 font-semibold",
                                "w-full text-left p-2 rounded-md text-sm hover:bg-gray-100",
                            ),
                        ),
                    ),
                    class_name="space-y-1",
                ),
                class_name="mb-4",
            ),
            rx.el.label(
                rx.el.input(
                    type="checkbox",
                    on_change=GapAnalysisState.toggle_affects_stack_filter,
                    checked=GapAnalysisState.filters["affects_stack"],
                    class_name="mr-2 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500",
                ),
                rx.el.span(
                    "Affects My Stack Only",
                    class_name="text-sm font-medium text-gray-700",
                ),
                class_name="flex items-center mb-4",
            ),
            rx.el.button(
                "Clear All Filters",
                on_click=GapAnalysisState.clear_all_filters,
                class_name="w-full text-sm text-center py-2 bg-gray-200 rounded-md hover:bg-gray-300 font-medium",
            ),
            class_name="p-4",
        ),
        class_name=rx.cond(
            GapAnalysisState.is_filter_panel_open,
            "fixed top-0 right-0 h-full w-72 bg-white shadow-lg z-30 transform-none transition-transform duration-300",
            "fixed top-0 -right-72 h-full w-72 bg-white shadow-lg z-30 transition-transform duration-300",
        ),
    )


def visualizations() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h3(
                "CVSS Gap Score Distribution",
                class_name="text-lg font-semibold text-gray-800 mb-4",
            ),
            rx.recharts.bar_chart(
                rx.recharts.cartesian_grid(vertical=False, class_name="opacity-50"),
                rx.recharts.graphing_tooltip(cursor=False),
                rx.recharts.bar(data_key="count", fill="#8884d8"),
                rx.recharts.x_axis(data_key="score"),
                rx.recharts.y_axis(allow_decimals=False),
                data=GapAnalysisState.cvss_gap_distribution,
                height=300,
            ),
            class_name="bg-white p-6 rounded-lg shadow-sm border",
        ),
        rx.el.div(
            rx.el.h3(
                "CPE Gap Score Distribution",
                class_name="text-lg font-semibold text-gray-800 mb-4",
            ),
            rx.recharts.bar_chart(
                rx.recharts.cartesian_grid(vertical=False, class_name="opacity-50"),
                rx.recharts.graphing_tooltip(cursor=False),
                rx.recharts.bar(data_key="count", fill="#82ca9d"),
                rx.recharts.x_axis(data_key="score"),
                rx.recharts.y_axis(allow_decimals=False),
                data=GapAnalysisState.cpe_gap_distribution,
                height=300,
            ),
            class_name="bg-white p-6 rounded-lg shadow-sm border",
        ),
        rx.el.div(
            rx.el.h3(
                "Monthly Backlog Growth",
                class_name="text-lg font-semibold text-gray-800 mb-4",
            ),
            rx.recharts.line_chart(
                rx.recharts.cartesian_grid(vertical=False, class_name="opacity-50"),
                rx.recharts.graphing_tooltip(cursor=False),
                rx.recharts.line(data_key="count", type_="natural", stroke="#ff7300"),
                rx.recharts.x_axis(data_key="month"),
                rx.recharts.y_axis(allow_decimals=False),
                data=GapAnalysisState.monthly_backlog_growth,
                height=300,
            ),
            class_name="bg-white p-6 rounded-lg shadow-sm border col-span-2",
        ),
        class_name="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8",
    )


def gap_analysis_page() -> rx.Component:
    """The Gap Intelligence Dashboard page content."""
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.h1(
                    "Gap Intelligence Dashboard",
                    class_name="text-3xl font-bold text-gray-800",
                ),
                rx.el.p(
                    "Global view of NVD enrichment gaps across all CVEs",
                    class_name="text-gray-600 mt-1",
                ),
            ),
            rx.el.button(
                rx.icon("sliders-horizontal", class_name="mr-2 h-4 w-4"),
                "Filters",
                on_click=GapAnalysisState.toggle_filter_panel,
                class_name="flex items-center text-sm bg-blue-500 text-white px-3 py-1.5 rounded-md font-medium hover:bg-blue-600",
            ),
            class_name="flex justify-between items-center mb-8",
        ),
        rx.el.div(
            metric_card(
                "Total Gaps Found",
                GapAnalysisState.total_gaps_count,
                "+1.2%",
                "Total number of CVEs with identified data gaps.",
            ),
            metric_card(
                "Avg. Enrichment Time",
                GapAnalysisState.avg_enrichment_time.to_string() + " days",
                "-3.4%",
                "Average number of days between CVE publication and full enrichment.",
            ),
            metric_card(
                "Worst Offender",
                GapAnalysisState.worst_offenders[0]["cve_id"].to_string(),
                GapAnalysisState.worst_offenders[0]["time_gap_days"].to_string()
                + " days",
                "The CVE that has been waiting the longest for enrichment.",
            ),
            class_name="grid grid-cols-1 md:grid-cols-3 gap-6",
        ),
        visualizations(),
        filter_panel(),
        class_name="p-8",
        on_mount=GapAnalysisState.load_initial_data,
    )