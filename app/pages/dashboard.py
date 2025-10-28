import reflex as rx
from app.states.dashboard_state import DashboardState, SEVERITY_COLORS
from app.state import AppState
from app.components.upgrade_prompts import pro_badge, locked_feature
from typing import Any


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
            class_name="bg-white p-6 rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow duration-300 cursor-pointer",
        ),
        label=tooltip,
    )


def filter_panel() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h3("Filters", class_name="text-lg font-semibold text-gray-800"),
            rx.el.button(
                rx.icon("x", class_name="h-5 w-5"),
                on_click=DashboardState.toggle_filter_panel,
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
                    placeholder="CVE ID, description...",
                    on_change=DashboardState.set_search_term.debounce(300),
                    default_value=DashboardState.filters["search_term"],
                    class_name="w-full p-2 border rounded-md text-sm",
                ),
                class_name="mb-4",
            ),
            rx.el.div(
                rx.el.label(
                    "Date Range", class_name="text-sm font-medium text-gray-700 mb-1"
                ),
                rx.el.select(
                    rx.foreach(
                        [
                            ("7", "Last 7 Days"),
                            ("30", "Last 30 Days"),
                            ("90", "Last 90 Days"),
                        ],
                        lambda option: rx.el.option(option[1], value=option[0]),
                    ),
                    value=DashboardState.filters["date_range"],
                    on_change=DashboardState.set_date_range,
                    class_name="w-full p-2 border rounded-md text-sm",
                ),
                class_name="mb-4",
            ),
            rx.el.div(
                rx.el.label(
                    "Severity", class_name="text-sm font-medium text-gray-700 mb-2"
                ),
                rx.el.div(
                    rx.foreach(
                        list(SEVERITY_COLORS.keys()),
                        lambda severity: rx.el.button(
                            severity.capitalize(),
                            on_click=lambda: DashboardState.toggle_severity_filter(
                                severity
                            ),
                            class_name=rx.cond(
                                DashboardState.filters["severity"].contains(severity),
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
                    on_change=DashboardState.toggle_kev_filter,
                    checked=DashboardState.filters["is_kev"],
                    class_name="mr-2 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500",
                ),
                rx.el.span(
                    "CISA KEV Only", class_name="text-sm font-medium text-gray-700"
                ),
                class_name="flex items-center",
            ),
            class_name="p-4",
        ),
        class_name=rx.cond(
            DashboardState.is_filter_panel_open,
            "fixed top-0 right-0 h-full w-72 bg-white shadow-lg z-30 transform-none transition-transform duration-300",
            "fixed top-0 -right-72 h-full w-72 bg-white shadow-lg z-30 transition-transform duration-300",
        ),
    )


def header_cell(title: str, key: str) -> rx.Component:
    return rx.el.th(
        rx.el.button(
            rx.el.span(title),
            rx.cond(
                DashboardState.sort_by[0] == key,
                rx.icon(
                    rx.cond(
                        DashboardState.sort_by[1] == "asc", "arrow-up", "arrow-down"
                    ),
                    class_name="h-4 w-4 ml-1",
                ),
                None,
            ),
            on_click=lambda: DashboardState.set_sort(key),
            class_name="flex items-center font-semibold text-gray-600 hover:text-gray-900 transition-colors",
        ),
        class_name="p-3 text-left text-sm",
    )


def cve_table_row(cve: dict) -> rx.Component:
    return rx.fragment(
        rx.el.tr(
            rx.el.td(
                rx.el.input(
                    type="checkbox",
                    on_change=lambda: DashboardState.toggle_row_selection(cve["id"]),
                    checked=DashboardState.selected_rows.contains(cve["id"]),
                    class_name="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500",
                ),
                class_name="p-3",
            ),
            rx.el.td(
                rx.el.button(
                    rx.icon(
                        rx.cond(
                            DashboardState.expanded_rows.contains(cve["id"]),
                            "chevron-down",
                            "chevron-right",
                        ),
                        class_name="h-4 w-4",
                    ),
                    on_click=lambda: DashboardState.toggle_row_expansion(cve["id"]),
                    class_name="p-1 rounded-full hover:bg-gray-200",
                ),
                class_name="p-3",
            ),
            rx.el.td(cve["id"], class_name="p-3 font-mono text-sm"),
            rx.el.td(
                rx.el.span(
                    cve["severity"],
                    class_name="px-2 py-1 text-xs font-semibold rounded-full w-fit",
                    style={
                        "backgroundColor": SEVERITY_COLORS.get(
                            cve["severity"].to(str), "#9ca3af"
                        ),
                        "color": "white",
                    },
                ),
                class_name="p-3",
            ),
            rx.el.td(cve["time_gap"].to_string() + " days", class_name="p-3 text-sm"),
            rx.el.td(cve["tech_match"].to_string() + "%", class_name="p-3 text-sm"),
            rx.el.td(
                cve["universal_risk_score"].to_string(),
                class_name="p-3 text-sm font-bold",
            ),
            rx.el.td(cve["published_date"].split("T")[0], class_name="p-3 text-sm"),
            class_name="border-b hover:bg-gray-50 transition-colors",
        ),
        rx.cond(
            DashboardState.expanded_rows.contains(cve["id"]),
            rx.el.tr(
                rx.el.td(
                    rx.el.div(
                        rx.el.h4("Full Description", class_name="font-semibold mb-1"),
                        rx.el.p(
                            cve["description"], class_name="text-sm text-gray-600 mb-4"
                        ),
                        rx.el.h4("Affected Product", class_name="font-semibold mb-1"),
                        rx.el.p(
                            f"{cve['vendor']}/{cve['product']}:{cve['version']}",
                            class_name="text-sm font-mono",
                        ),
                        class_name="bg-gray-50 p-4 rounded-md",
                    ),
                    col_span=7,
                    class_name="p-0",
                )
            ),
            None,
        ),
    )


def hero_metrics() -> rx.Component:
    return rx.el.div(
        metric_card(
            "Awaiting Enrichment",
            DashboardState.awaiting_enrichment_count,
            "+5.2%",
            "CVEs in your tech stack without full NVD data.",
        ),
        metric_card(
            "Avg. Enrichment Lag",
            DashboardState.average_enrichment_lag,
            "-2 days",
            "Average time from CVE publication to full enrichment.",
        ),
        metric_card(
            "Critical KEVs",
            DashboardState.critical_kev_count,
            "+2",
            "Critical CVEs in CISA's Known Exploited Vulnerabilities catalog.",
        ),
        class_name="grid grid-cols-1 md:grid-cols-3 gap-6",
    )


def visualizations() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h3(
                "CVEs Over Time (Last 90 Days)",
                class_name="text-lg font-semibold text-gray-800 mb-4",
            ),
            rx.recharts.area_chart(
                rx.recharts.cartesian_grid(vertical=False, class_name="opacity-50"),
                rx.recharts.graphing_tooltip(cursor=False),
                rx.recharts.area(
                    data_key="count",
                    type_="natural",
                    stroke="#3b82f6",
                    fill="#3b82f6",
                    fill_opacity=0.3,
                ),
                rx.recharts.x_axis(
                    data_key="date", tick_line=False, axis_line=False, tick_margin=8
                ),
                rx.recharts.y_axis(
                    allow_decimals=False,
                    tick_line=False,
                    axis_line=False,
                    tick_margin=8,
                ),
                data=DashboardState.cves_over_time,
                height=300,
            ),
            class_name="bg-white p-6 rounded-lg shadow-sm border",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.h3(
                    "Severity Distribution",
                    class_name="text-lg font-semibold text-gray-800 mb-4",
                ),
                rx.recharts.pie_chart(
                    rx.recharts.graphing_tooltip(
                        content_style={
                            "background": "white",
                            "border": "1px solid #ccc",
                        }
                    ),
                    rx.recharts.pie(
                        data=DashboardState.severity_distribution,
                        data_key="value",
                        name_key="name",
                        cx="50%",
                        cy="50%",
                        outer_radius=80,
                        label=True,
                        stroke="#fff",
                        stroke_width=2,
                    ),
                    height=300,
                ),
                class_name="bg-white p-6 rounded-lg shadow-sm border",
            ),
            rx.el.div(
                rx.el.h3(
                    "Tech Stack Exposure",
                    class_name="text-lg font-semibold text-gray-800 mb-4",
                ),
                rx.recharts.bar_chart(
                    rx.recharts.cartesian_grid(vertical=False, class_name="opacity-50"),
                    rx.recharts.graphing_tooltip(cursor=False),
                    rx.recharts.bar(data_key="count", fill="#14b8a6"),
                    rx.recharts.x_axis(
                        data_key="name", tick_line=False, axis_line=False, tick_margin=8
                    ),
                    rx.recharts.y_axis(
                        allow_decimals=False,
                        tick_line=False,
                        axis_line=False,
                        tick_margin=8,
                    ),
                    data=DashboardState.tech_stack_distribution,
                    layout="vertical",
                    height=300,
                    margin={"left": 30},
                ),
                class_name="bg-white p-6 rounded-lg shadow-sm border",
            ),
            class_name="grid grid-cols-1 lg:grid-cols-2 gap-6",
        ),
        class_name="mt-8 grid grid-cols-1 gap-6",
    )


def cve_table() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h3(
                "Actionable Risk Register",
                class_name="text-lg font-semibold text-gray-800",
            ),
            rx.el.div(
                rx.cond(
                    AppState.can_export_csv,
                    rx.el.button(
                        "Export CSV",
                        pro_badge(),
                        class_name="flex items-center text-sm bg-gray-200 px-3 py-1.5 rounded-md font-medium hover:bg-gray-300",
                    ),
                    locked_feature(feature_name="CSV Export", required_tier="pro"),
                ),
                rx.el.button(
                    rx.icon("sliders-horizontal", class_name="mr-2 h-4 w-4"),
                    "Filters",
                    on_click=DashboardState.toggle_filter_panel,
                    class_name="flex items-center text-sm bg-blue-500 text-white px-3 py-1.5 rounded-md font-medium hover:bg-blue-600",
                ),
            ),
            class_name="flex items-center justify-between mb-4",
        ),
        rx.el.div(
            rx.el.table(
                rx.el.thead(
                    rx.el.tr(
                        rx.el.th(
                            rx.el.input(
                                type="checkbox",
                                on_change=DashboardState.toggle_select_all,
                                class_name="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500",
                            ),
                            class_name="p-3",
                        ),
                        rx.el.th("", class_name="p-3"),
                        header_cell("CVE ID", "id"),
                        header_cell("Severity", "severity"),
                        header_cell("Time Gap", "time_gap"),
                        header_cell("Tech Match", "tech_match"),
                        header_cell("Universal Risk", "universal_risk_score"),
                        header_cell("Published", "published_date"),
                    )
                ),
                rx.el.tbody(rx.foreach(DashboardState.filtered_cves, cve_table_row)),
                class_name="w-full",
            ),
            class_name="overflow-x-auto rounded-lg border border-gray-200 bg-white",
        ),
    )


def scanner_vs_aperture_view() -> rx.Component:
    return rx.el.div(
        rx.el.h2(
            "Scanner Blind Spots",
            class_name="text-2xl font-bold text-gray-800 mb-4 text-center",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.h3(
                    "Static Scanner View (Yesterday)",
                    class_name="text-xl font-semibold text-gray-700 mb-3",
                ),
                rx.data_table(
                    data=DashboardState.scanner_view_cves,
                    columns=[
                        {"title": "CVE ID", "type": "str"},
                        {"title": "Vendor", "type": "str"},
                        {"title": "Product", "type": "str"},
                    ],
                    pagination=False,
                    sort=False,
                ),
                class_name="bg-white p-6 rounded-lg shadow-sm border",
            ),
            rx.el.div(
                rx.el.h3(
                    "Aperture Blind Spots (Today)",
                    class_name="text-xl font-semibold text-teal-700 mb-3",
                ),
                rx.data_table(
                    data=DashboardState.blind_spot_cves,
                    columns=[
                        {"title": "CVE ID", "type": "str", "key": "id"},
                        {"title": "Severity", "type": "str", "key": "severity"},
                        {"title": "Product", "type": "str", "key": "product"},
                    ],
                    pagination=False,
                    sort=False,
                ),
                class_name="bg-white p-6 rounded-lg shadow-sm border border-teal-300",
            ),
            class_name="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-6",
        ),
        class_name="mt-12",
    )


def dashboard_page() -> rx.Component:
    """The new interactive dashboard page content."""
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.h1(
                    "Main Dashboard", class_name="text-3xl font-bold text-gray-800"
                ),
                rx.el.div(
                    rx.el.select(
                        rx.foreach(
                            DashboardState.views,
                            lambda view: rx.el.option(view["name"], value=view["name"]),
                        ),
                        value=DashboardState.active_view,
                        on_change=DashboardState.load_view,
                        class_name="text-sm font-medium border-gray-300 rounded-md shadow-sm",
                    ),
                    rx.el.div(
                        rx.el.input(
                            placeholder="New View Name...",
                            on_change=DashboardState.set_new_view_name,
                            default_value=DashboardState.new_view_name,
                            class_name="text-sm rounded-l-md border-gray-300",
                        ),
                        rx.el.button(
                            "Save View",
                            on_click=DashboardState.save_current_view,
                            class_name="bg-blue-500 text-white px-3 py-1.5 rounded-r-md text-sm font-semibold hover:bg-blue-600",
                        ),
                        class_name="flex",
                    ),
                    class_name="flex items-center gap-4",
                ),
                class_name="flex justify-between items-center mb-8",
            ),
            rx.cond(
                DashboardState.is_loading,
                rx.el.div(
                    rx.el.div(class_name="h-28 bg-gray-200 rounded-lg animate-pulse"),
                    rx.el.div(class_name="h-28 bg-gray-200 rounded-lg animate-pulse"),
                    rx.el.div(class_name="h-28 bg-gray-200 rounded-lg animate-pulse"),
                    rx.el.div(
                        class_name="h-80 bg-gray-200 rounded-lg animate-pulse col-span-2"
                    ),
                    rx.el.div(class_name="h-80 bg-gray-200 rounded-lg animate-pulse"),
                    class_name="grid grid-cols-1 md:grid-cols-3 gap-6",
                ),
                rx.el.div(
                    hero_metrics(),
                    visualizations(),
                    rx.el.div(cve_table(), class_name="mt-8"),
                    scanner_vs_aperture_view(),
                ),
            ),
        ),
        filter_panel(),
        class_name="p-8 font-['Montserrat']",
        on_mount=DashboardState.load_initial_data,
    )