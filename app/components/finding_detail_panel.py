import reflex as rx
from app.states.finding_detail_state import FindingDetailState
from app.states.feedback_state import FeedbackState


def risk_badge(score: rx.Var[float]) -> rx.Component:
    score_int = score.to(int)
    return rx.el.span(
        score_int.to_string(),
        class_name=rx.cond(
            score_int >= 90,
            "px-3 py-1 text-sm rounded-full bg-red-100 text-red-800 font-bold",
            rx.cond(
                score_int >= 70,
                "px-3 py-1 text-sm rounded-full bg-orange-100 text-orange-800 font-bold",
                rx.cond(
                    score_int >= 40,
                    "px-3 py-1 text-sm rounded-full bg-yellow-100 text-yellow-800 font-bold",
                    "px-3 py-1 text-sm rounded-full bg-green-100 text-green-800 font-bold",
                ),
            ),
        ),
    )


def detail_section(icon_name: str, title: str, content: rx.Component) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(icon_name, class_name="h-5 w-5 text-gray-500"),
            rx.el.h3(title, class_name="text-lg font-bold text-gray-800"),
            class_name="flex items-center gap-3 mb-4",
        ),
        content,
        class_name="py-6 border-b border-gray-200",
    )


def key_value_pair(key: str, value: rx.Var) -> rx.Component:
    return rx.el.div(
        rx.el.p(key, class_name="text-sm text-gray-600"),
        rx.el.p(value.to_string(), class_name="text-sm font-semibold text-gray-900"),
        class_name="flex justify-between items-center",
    )


def explainability_section() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("brain", class_name="h-5 w-5 text-purple-600"),
            rx.el.h3("Why This Score?", class_name="text-lg font-bold"),
            rx.el.button(
                "Expand",
                on_click=FindingDetailState.toggle_explainability_modal,
                class_name="text-sm text-purple-600 hover:underline font-semibold",
            ),
            class_name="flex items-center justify-between mb-4",
        ),
        rx.el.div(
            rx.foreach(
                FindingDetailState.top_contributing_features,
                lambda feature: rx.el.div(
                    rx.el.div(
                        rx.el.span(feature["name"], class_name="font-medium text-sm"),
                        rx.el.span(
                            f"{feature['weight']}%", class_name="text-sm text-gray-500"
                        ),
                        class_name="flex justify-between mb-1",
                    ),
                    rx.el.div(
                        rx.el.div(
                            class_name="h-3 bg-purple-500 rounded",
                            style={"width": feature["weight"].to_string() + "%"},
                        ),
                        class_name="w-full bg-gray-200 rounded h-3",
                    ),
                    class_name="mb-3",
                ),
            ),
            class_name="space-y-2",
        ),
        rx.el.div(
            rx.el.span("Model Confidence: ", class_name="text-sm text-gray-600"),
            rx.el.span(
                (
                    FindingDetailState.selected_finding["confidence_score"] * 100
                ).to_string()
                + "%",
                class_name="font-bold text-purple-600",
            ),
            class_name="mt-4 p-3 bg-purple-50 rounded-lg text-center",
        ),
        class_name="bg-white p-4 rounded-lg border-2 border-dashed border-purple-200",
    )


def explainability_modal() -> rx.Component:
    return rx.radix.primitives.dialog.root(
        rx.radix.primitives.dialog.portal(
            rx.radix.primitives.dialog.overlay(
                class_name="fixed inset-0 bg-black/50 z-40"
            ),
            rx.radix.primitives.dialog.content(
                rx.radix.primitives.dialog.title(
                    rx.el.div(
                        rx.icon("brain", class_name="h-6 w-6 text-purple-600"),
                        "Model Explainability: Deep Dive",
                        class_name="flex items-center gap-2 text-2xl font-bold",
                    )
                ),
                rx.el.div(
                    rx.el.h4(
                        "All Contributing Features", class_name="font-bold mb-3 mt-6"
                    ),
                    rx.el.div(
                        rx.foreach(
                            FindingDetailState.all_explainability_features,
                            lambda feature: rx.el.div(
                                rx.el.div(
                                    rx.el.span(
                                        feature["name"],
                                        class_name="text-sm font-medium",
                                    ),
                                    rx.el.span(
                                        f"{feature['weight']}%",
                                        class_name="text-sm font-mono",
                                    ),
                                    class_name="flex justify-between",
                                ),
                                rx.el.div(
                                    rx.el.div(
                                        class_name="h-2 bg-gradient-to-r from-purple-400 to-purple-600 rounded",
                                        style={
                                            "width": feature["weight"].to_string() + "%"
                                        },
                                    ),
                                    class_name="w-full bg-gray-200 rounded h-2 mt-1",
                                ),
                                rx.el.p(
                                    feature["description"],
                                    class_name="text-xs text-gray-500 mt-1",
                                ),
                                class_name="mb-4",
                            ),
                        ),
                        class_name="max-h-80 overflow-y-auto p-4 bg-gray-50 rounded-lg",
                    ),
                ),
                rx.el.div(
                    rx.el.h4("Decision Path", class_name="font-bold mb-3 mt-6"),
                    rx.el.div(
                        rx.el.p(
                            "The model considered these factors in sequence:",
                            class_name="text-sm mb-2",
                        ),
                        rx.el.ol(
                            rx.el.li(
                                "EPSS Score (0.95) → High exploitation probability"
                            ),
                            rx.el.li("Public IP exposure → Increased attack surface"),
                            rx.el.li("PoC availability → Active threat"),
                            rx.el.li("CVE age (< 30 days) → Recent discovery"),
                            rx.el.li("Affected product in tech stack → Direct impact"),
                            class_name="list-decimal ml-6 space-y-2 text-sm text-gray-700",
                        ),
                        class_name="p-4 bg-gray-50 rounded-lg",
                    ),
                ),
                rx.radix.primitives.dialog.close(
                    rx.el.button(
                        "Close",
                        class_name="mt-6 w-full bg-gray-200 text-gray-800 py-2 rounded-md font-semibold hover:bg-gray-300",
                    )
                ),
                class_name="bg-white p-6 rounded-xl shadow-2xl w-full max-w-2xl",
            ),
        ),
        open=FindingDetailState.show_explainability_modal,
        on_open_change=FindingDetailState.toggle_explainability_modal,
    )


def finding_detail_panel() -> rx.Component:
    finding = FindingDetailState.selected_finding
    return rx.el.div(
        rx.cond(
            FindingDetailState.is_loading,
            rx.el.div(
                rx.spinner(class_name="h-8 w-8 text-purple-500"),
                class_name="flex items-center justify-center h-full",
            ),
            rx.cond(
                finding,
                rx.el.div(
                    rx.el.div(
                        rx.el.div(
                            rx.el.h2(
                                finding["cve_id"],
                                class_name="text-xl font-bold text-gray-900 truncate",
                            ),
                            risk_badge(finding["predicted_impact_score"]),
                        ),
                        rx.el.button(
                            rx.icon("x", class_name="h-5 w-5"),
                            on_click=FindingDetailState.close_finding_detail,
                            class_name="p-2 rounded-full text-gray-500 hover:bg-gray-200",
                        ),
                        class_name="flex items-center justify-between p-4 border-b border-gray-200",
                    ),
                    rx.el.div(
                        detail_section(
                            "bar_chart",
                            "Risk Overview",
                            rx.el.div(
                                key_value_pair(
                                    "Universal Risk", finding["predicted_impact_score"]
                                ),
                                key_value_pair(
                                    "Predicted Severity", finding["predicted_severity"]
                                ),
                                key_value_pair(
                                    "Confidence",
                                    (finding["confidence_score"] * 100).to_string()
                                    + "%",
                                ),
                                class_name="space-y-2",
                            ),
                        ),
                        detail_section(
                            "brain_circuit", "Explainability", explainability_section()
                        ),
                        detail_section(
                            "target",
                            "ML Predictions",
                            rx.el.div(
                                key_value_pair(
                                    "Predicted Impact Score",
                                    finding["predicted_impact_score"],
                                ),
                                key_value_pair(
                                    "Exploitation Likelihood",
                                    finding["exploitation_likelihood"],
                                ),
                                key_value_pair(
                                    "Risk Category", finding["risk_category"]
                                ),
                                key_value_pair(
                                    "Attack Complexity", finding["attack_complexity"]
                                ),
                                class_name="space-y-2",
                            ),
                        ),
                        detail_section(
                            "search",
                            "Extracted Intelligence",
                            rx.el.div(
                                key_value_pair(
                                    "Products",
                                    finding["extracted_products"].to_string(),
                                ),
                                key_value_pair(
                                    "Attack Vectors",
                                    finding["extracted_attack_vectors"].to_string(),
                                ),
                                key_value_pair(
                                    "Keywords", finding["technical_keywords"].join(", ")
                                ),
                                class_name="space-y-2",
                            ),
                        ),
                        detail_section(
                            "file_text",
                            "Raw CVE Data",
                            rx.el.div(
                                rx.el.p(
                                    "Description",
                                    class_name="text-sm font-semibold mb-1",
                                ),
                                rx.el.p(
                                    finding["raw_description"],
                                    class_name="text-xs text-gray-600 leading-relaxed",
                                ),
                                rx.el.p(
                                    "References",
                                    class_name="text-sm font-semibold mt-3 mb-1",
                                ),
                                rx.foreach(
                                    finding["raw_references"],
                                    lambda ref: rx.el.a(
                                        ref,
                                        href=ref,
                                        class_name="text-xs text-blue-600 block truncate",
                                        target="_blank",
                                    ),
                                ),
                                class_name="space-y-1",
                            ),
                        ),
                        detail_section(
                            "cpu",
                            "Model Metadata",
                            rx.el.div(
                                key_value_pair(
                                    "Model Version", finding["model_version"]
                                ),
                                key_value_pair(
                                    "Processing Time",
                                    finding["processing_time_ms"].to_string() + "ms",
                                ),
                                key_value_pair(
                                    "Inference Timestamp",
                                    finding["inference_timestamp"],
                                ),
                                class_name="space-y-2",
                            ),
                        ),
                        detail_section(
                            "message-square-plus",
                            "Human-in-the-Loop Feedback",
                            feedback_panel(),
                        ),
                        class_name="p-4",
                    ),
                    explainability_modal(),
                ),
                rx.el.div(
                    "No finding selected.", class_name="p-8 text-center text-gray-500"
                ),
            ),
        ),
        class_name=rx.cond(
            FindingDetailState.is_panel_open,
            "fixed right-0 top-0 h-full w-full md:w-[450px] bg-white shadow-2xl z-40 overflow-y-auto transform transition-transform duration-300 ease-in-out translate-x-0",
            "fixed right-0 top-0 h-full w-full md:w-[450px] bg-white shadow-2xl z-40 overflow-y-auto transform transition-transform duration-300 ease-in-out translate-x-full",
        ),
    )


def feedback_panel() -> rx.Component:
    feedback = FeedbackState.feedback_for_finding
    is_submitting = FeedbackState.is_submitting
    finding_id = FindingDetailState.selected_finding["id"]
    return rx.el.div(
        rx.cond(
            feedback,
            rx.el.div(
                rx.el.p(
                    "Your feedback has been recorded:",
                    class_name="text-sm text-gray-600 mb-2",
                ),
                rx.el.div(
                    rx.el.span(
                        feedback["label"].to_string().replace("_", " ").capitalize(),
                        class_name=rx.cond(
                            feedback["label"] == "exploitable",
                            "px-3 py-1 text-sm font-bold rounded-full bg-green-100 text-green-800",
                            "px-3 py-1 text-sm font-bold rounded-full bg-gray-100 text-gray-800",
                        ),
                    ),
                    rx.el.button(
                        "Undo Feedback",
                        on_click=FeedbackState.undo_feedback,
                        is_loading=is_submitting,
                        class_name="text-sm text-gray-500 hover:underline",
                    ),
                    class_name="flex items-center justify-between",
                ),
                rx.cond(
                    feedback["notes"],
                    rx.el.div(
                        rx.el.p("Your Notes:", class_name="text-xs font-bold mt-2"),
                        rx.el.p(feedback["notes"], class_name="text-xs italic"),
                    ),
                    None,
                ),
            ),
            rx.el.div(
                rx.el.p(
                    "Is this finding accurate? Help improve our model.",
                    class_name="text-sm text-gray-600 mb-4",
                ),
                rx.el.div(
                    rx.el.button(
                        rx.icon("square_check", class_name="h-4 w-4 mr-2"),
                        "Confirm Exploitability",
                        on_click=lambda: FeedbackState.submit_feedback(
                            finding_id, "exploitable", 5, ""
                        ),
                        is_loading=is_submitting,
                        class_name="flex-1 flex items-center justify-center bg-green-500 text-white px-4 py-2 rounded-md font-semibold hover:bg-green-600 transition",
                    ),
                    rx.el.button(
                        rx.icon("circle_x", class_name="h-4 w-4 mr-2"),
                        "Mark as False Positive",
                        on_click=lambda: FeedbackState.submit_feedback(
                            finding_id, "false_positive", 1, ""
                        ),
                        is_loading=is_submitting,
                        class_name="flex-1 flex items-center justify-center bg-gray-500 text-white px-4 py-2 rounded-md font-semibold hover:bg-gray-600 transition",
                    ),
                    class_name="flex gap-2",
                ),
            ),
        ),
        class_name="bg-gray-50 p-4 rounded-lg border",
    )