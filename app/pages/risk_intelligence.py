import reflex as rx
from app.states.risk_intelligence_state import RiskIntelligenceState
from app.states.finding_detail_state import FindingDetailState
from app.components.finding_detail_panel import finding_detail_panel


def score_badge(score: rx.Var[float]) -> rx.Component:
    return rx.el.span(
        score.to_string(),
        class_name=rx.cond(
            score > 90,
            "bg-red-100 text-red-800 text-xs font-medium px-2.5 py-0.5 rounded-full",
            rx.cond(
                score > 70,
                "bg-orange-100 text-orange-800 text-xs font-medium px-2.5 py-0.5 rounded-full",
                rx.cond(
                    score > 40,
                    "bg-yellow-100 text-yellow-800 text-xs font-medium px-2.5 py-0.5 rounded-full",
                    "bg-green-100 text-green-800 text-xs font-medium px-2.5 py-0.5 rounded-full",
                ),
            ),
        ),
    )


def header_cell(title: str, key: str) -> rx.Component:
    return rx.el.th(
        rx.el.button(
            rx.el.span(title),
            rx.cond(
                RiskIntelligenceState.sort_by[0] == key,
                rx.icon(
                    rx.cond(
                        RiskIntelligenceState.sort_by[1] == "asc",
                        "arrow-up",
                        "arrow-down",
                    ),
                    class_name="h-4 w-4 ml-1",
                ),
                None,
            ),
            on_click=lambda: RiskIntelligenceState.set_sort(key),
            class_name="flex items-center font-semibold text-gray-600 hover:text-gray-900 transition-colors",
        ),
        class_name="p-3 text-left text-sm",
    )


def cve_table_row(cve: dict) -> rx.Component:
    return rx.el.tr(
        rx.el.td(cve["cve_id"], class_name="p-3 font-mono text-sm"),
        rx.el.td(score_badge(cve["universal_risk_score"]), class_name="p-3"),
        rx.el.td(cve["cvss_score"].to_string(), class_name="p-3 text-sm"),
        rx.el.td(cve["epss_score"].to_string(), class_name="p-3 text-sm"),
        rx.el.td(
            rx.cond(
                cve["is_kev"],
                rx.icon("square_check", class_name="h-5 w-5 text-red-500"),
                rx.icon("minus", class_name="h-5 w-5 text-gray-300"),
            ),
            class_name="p-3 text-center",
        ),
        rx.el.td(cve["agreement"].to_string(), class_name="p-3 text-sm"),
        rx.el.td(
            rx.el.button(
                "Details",
                on_click=lambda: FindingDetailState.open_finding_detail(cve["cve_id"]),
                class_name="text-teal-600 hover:underline text-sm font-semibold",
            ),
            class_name="p-3",
        ),
        class_name="border-b hover:bg-gray-50 transition-colors",
    )


from app.states.llm_analysis_state import LlmAnalysisState, PROVIDER_CONFIG


def llm_analysis_section() -> rx.Component:
    cve_id = RiskIntelligenceState.selected_cve["cve_id"]
    analysis = LlmAnalysisState.analysis_result.get(cve_id, {})
    return rx.el.div(
        rx.el.h3(
            "AI-Powered Analysis",
            class_name="text-xl font-bold text-gray-800 mt-6 mb-4",
        ),
        rx.cond(
            LlmAnalysisState.is_analyzing,
            rx.el.div(
                rx.el.h4("Generating Analysis...", class_name="font-semibold mb-2"),
                rx.el.pre(
                    LlmAnalysisState.streaming_content,
                    class_name="text-sm p-4 bg-gray-900 text-white rounded-md whitespace-pre-wrap",
                ),
                class_name="animate-pulse",
            ),
            rx.cond(
                analysis,
                rx.el.div(
                    rx.el.div(
                        rx.el.h5("Executive Summary", class_name="font-bold"),
                        rx.el.p(
                            analysis.get("executive_summary"),
                            class_name="text-sm text-gray-700",
                        ),
                    ),
                    rx.el.div(
                        rx.el.h5("Recommended Actions", class_name="font-bold mt-4"),
                        rx.el.ul(
                            rx.foreach(
                                analysis.get("recommended_actions", []),
                                lambda action: rx.el.li(
                                    action, class_name="text-sm text-gray-700"
                                ),
                            ),
                            class_name="list-disc list-inside",
                        ),
                    ),
                    class_name="space-y-2",
                ),
                rx.el.div(
                    rx.el.button(
                        "Analyze with AI",
                        on_click=lambda: LlmAnalysisState.analyze_cve(
                            RiskIntelligenceState.selected_cve
                        ),
                        class_name="bg-teal-500 text-white px-4 py-2 rounded-md font-semibold hover:bg-teal-600",
                    ),
                    rx.el.p(
                        f"Cost: {LlmAnalysisState.current_provider_cost} credits",
                        class_name="text-xs text-gray-500 mt-1",
                    ),
                ),
            ),
        ),
        class_name="mt-4 pt-4 border-t",
    )


def cve_detail_modal() -> rx.Component:
    return rx.radix.primitives.dialog.root(
        rx.radix.primitives.dialog.content(
            rx.cond(
                RiskIntelligenceState.selected_cve,
                rx.fragment(
                    rx.radix.primitives.dialog.title(
                        f"Risk Breakdown for {RiskIntelligenceState.selected_cve['cve_id']}",
                        class_name="text-2xl font-bold",
                    ),
                    rx.el.div(
                        rx.el.div(
                            rx.el.p(
                                "Universal Risk Score",
                                class_name="text-lg font-medium text-gray-700",
                            ),
                            rx.el.p(
                                RiskIntelligenceState.selected_cve[
                                    "universal_risk_score"
                                ].to_string(),
                                class_name="text-6xl font-bold text-teal-600",
                            ),
                            class_name="text-center",
                        ),
                        rx.el.div(
                            rx.recharts.pie_chart(
                                rx.recharts.graphing_tooltip(),
                                rx.recharts.pie(
                                    data=RiskIntelligenceState.selected_cve_breakdown,
                                    data_key="value",
                                    name_key="name",
                                    cx="50%",
                                    cy="50%",
                                    inner_radius=40,
                                    outer_radius=70,
                                    label=True,
                                    stroke="#fff",
                                    stroke_width=2,
                                ),
                                height=200,
                            ),
                            class_name="flex-shrink-0",
                        ),
                        class_name="flex items-center justify-between p-4 bg-gray-50 rounded-lg my-4",
                    ),
                    rx.el.div(
                        rx.el.h4("Framework Scores", class_name="font-semibold mb-2"),
                        rx.el.ul(
                            rx.el.li(
                                f"CVSS Score: {RiskIntelligenceState.selected_cve['cvss_score']}"
                            ),
                            rx.el.li(
                                f"EPSS Score: {RiskIntelligenceState.selected_cve['epss_score']}"
                            ),
                            rx.el.li(
                                f"SSVC Decision: {RiskIntelligenceState.selected_cve['ssvc_decision']}"
                            ),
                            rx.el.li(
                                f"In KEV: {RiskIntelligenceState.selected_cve['is_kev']}"
                            ),
                            class_name="list-disc list-inside text-sm text-gray-600",
                        ),
                    ),
                    llm_analysis_section(),
                ),
                rx.el.div("Loading..."),
            )
        ),
        open=RiskIntelligenceState.show_detail_modal,
        on_open_change=RiskIntelligenceState.close_detail_modal,
    )


def risk_intelligence_page() -> rx.Component:
    return rx.el.div(
        rx.el.h1(
            "Risk Intelligence Dashboard",
            class_name="text-3xl font-bold text-gray-800 mb-6",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.h3("Score Distribution", class_name="font-semibold mb-2"),
                rx.recharts.bar_chart(
                    rx.recharts.graphing_tooltip(),
                    rx.recharts.x_axis(data_key="range"),
                    rx.recharts.y_axis(allow_decimals=False),
                    rx.recharts.bar(data_key="count", fill="#14b8a6"),
                    data=RiskIntelligenceState.score_distribution,
                    height=200,
                ),
                class_name="bg-white p-4 rounded-lg shadow-sm border",
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8",
        ),
        rx.el.div(
            rx.el.table(
                rx.el.thead(
                    rx.el.tr(
                        header_cell("CVE ID", "cve_id"),
                        header_cell("Universal Risk", "universal_risk_score"),
                        header_cell("CVSS", "cvss_score"),
                        header_cell("EPSS", "epss_score"),
                        header_cell("KEV", "is_kev"),
                        header_cell("Agreement", "agreement"),
                        rx.el.th("Actions", class_name="p-3"),
                    )
                ),
                rx.el.tbody(
                    rx.foreach(RiskIntelligenceState.filtered_cves, cve_table_row)
                ),
                class_name="w-full",
            ),
            class_name="overflow-x-auto rounded-lg border border-gray-200 bg-white",
        ),
        cve_detail_modal(),
        finding_detail_panel(),
        rx.cond(
            FindingDetailState.is_panel_open,
            rx.el.div(
                on_click=FindingDetailState.close_finding_detail,
                class_name="fixed inset-0 bg-black bg-opacity-30 z-30",
            ),
            None,
        ),
        class_name="p-8 relative",
        on_mount=RiskIntelligenceState.load_all_cve_data,
    )