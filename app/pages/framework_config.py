import reflex as rx
from app.states.framework_config_state import FrameworkConfigState

WEIGHT_COLORS = {
    "cvss": "#3b82f6",
    "epss": "#14b8a6",
    "kev": "#ef4444",
    "ssvc": "#f97316",
    "lev": "#8b5cf6",
}


def weight_slider(framework: str, name: str) -> rx.Component:
    return rx.el.div(
        rx.el.label(name, class_name="font-medium text-gray-700"),
        rx.el.div(
            rx.el.input(
                type="range",
                min=0,
                max=1,
                step=0.05,
                key=f"slider-{framework}",
                default_value=FrameworkConfigState.weights[framework].to_string(),
                on_change=lambda value: FrameworkConfigState.adjust_weight(
                    value, framework
                ).throttle(100),
                class_name="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-teal-500",
            ),
            rx.el.span(
                FrameworkConfigState.weights[framework].to_string(),
                class_name="w-12 text-right text-sm font-mono text-gray-600",
            ),
            class_name="flex items-center gap-4 mt-2",
        ),
        class_name="mb-4",
    )


def score_preview() -> rx.Component:
    return rx.el.div(
        rx.el.h3(
            "Real-time Score Preview",
            class_name="text-xl font-semibold text-gray-800 mb-4",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    "Sample CVE: CVE-2024-21412 (High CVSS, High EPSS, KEV)",
                    class_name="text-sm text-gray-500 mb-4",
                ),
                rx.el.div(
                    rx.el.p(
                        "Universal Risk Score",
                        class_name="text-lg font-medium text-gray-700",
                    ),
                    rx.el.p(
                        FrameworkConfigState.preview_score.get(
                            "universal_risk_score", 0
                        ).to_string(),
                        class_name="text-5xl font-bold text-teal-600",
                    ),
                    class_name="text-center",
                ),
                class_name="flex-1",
            ),
            rx.el.div(
                rx.recharts.pie_chart(
                    rx.recharts.graphing_tooltip(),
                    rx.recharts.pie(
                        data=FrameworkConfigState.breakdown_data,
                        data_key="value",
                        name_key="name",
                        cx="50%",
                        cy="50%",
                        inner_radius=40,
                        outer_radius=70,
                        padding_angle=5,
                        label=True,
                        stroke="#fff",
                        stroke_width=2,
                    ),
                    height=250,
                ),
                class_name="flex-1",
            ),
            class_name="flex items-center justify-between gap-8",
        ),
        class_name="bg-white p-6 rounded-lg shadow-sm border border-gray-200",
    )


def ai_suggestion_card() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("sparkles", class_name="h-6 w-6 text-yellow-400"),
            rx.el.h4("AI-Powered Suggestion", class_name="text-lg font-semibold"),
            class_name="flex items-center gap-2",
        ),
        rx.el.p(
            "Based on your recent vulnerability trends, we recommend increasing the EPSS weight to 0.45 to better prioritize real-world threats.",
            class_name="text-sm text-gray-600 mt-2",
        ),
        rx.el.a(
            rx.el.button(
                "View All Recommendations",
                class_name="mt-4 text-sm font-medium text-teal-600 hover:underline",
            ),
            href="/recommendations",
        ),
        class_name="bg-yellow-50 p-6 rounded-lg border-2 border-dashed border-yellow-300 mt-8",
    )


def framework_config_page() -> rx.Component:
    """The framework configuration page content."""
    return rx.el.div(
        rx.el.div(
            rx.el.h1(
                "Framework Configuration", class_name="text-3xl font-bold text-gray-800"
            ),
            rx.el.p(
                "Customize the universal risk scoring engine to match your organization's risk appetite.",
                class_name="text-gray-600 mt-1",
            ),
            class_name="mb-8",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.h3(
                    "Scoring Weights",
                    class_name="text-xl font-semibold text-gray-800 mb-2",
                ),
                rx.el.p(
                    "Adjust the influence of each framework on the universal score. Weights must sum to 1.0.",
                    class_name="text-sm text-gray-500 mb-6",
                ),
                weight_slider("cvss", "CVSS v3.1"),
                weight_slider("epss", "EPSS"),
                weight_slider("kev", "CISA KEV"),
                weight_slider("ssvc", "SSVC"),
                weight_slider("lev", "LEV (Experimental)"),
                rx.el.div(
                    rx.el.p(
                        f"Total Weight: {FrameworkConfigState.total_weight}",
                        class_name="font-semibold",
                    ),
                    class_name=rx.cond(
                        FrameworkConfigState.total_weight == 1.0,
                        "text-green-600",
                        "text-red-600",
                    ),
                    style={"textAlign": "right"},
                ),
                class_name="bg-white p-6 rounded-lg shadow-sm border border-gray-200 mb-8",
            ),
            score_preview(),
            class_name="grid grid-cols-1 lg:grid-cols-2 gap-8",
        ),
        ai_suggestion_card(),
        ai_suggestion_card(),
        rx.el.div(
            rx.el.button(
                "Reset to Recommended",
                on_click=FrameworkConfigState.reset_to_recommended,
                class_name="bg-gray-200 text-gray-700 px-4 py-2 rounded-md font-semibold hover:bg-gray-300 transition",
            ),
            rx.el.button(
                "Save Configuration",
                on_click=FrameworkConfigState.save_config,
                is_loading=FrameworkConfigState.is_loading,
                class_name="bg-teal-500 text-white px-4 py-2 rounded-md font-semibold hover:bg-teal-600 transition",
            ),
            class_name="flex justify-end gap-4 mt-8",
        ),
        class_name="p-8",
        on_mount=FrameworkConfigState.load_config,
    )