import reflex as rx
from app.states.recommendation_state import RecommendationState, Recommendation


def recommendation_card(rec: Recommendation) -> rx.Component:
    rec_type_colors = {
        "adjust_weights": "bg-blue-100 text-blue-800",
        "change_provider": "bg-purple-100 text-purple-800",
        "enable_framework": "bg-green-100 text-green-800",
        "disable_framework": "bg-yellow-100 text-yellow-800",
    }
    rec_type_var = rx.Var.create(rec["recommendation_type"].to_string())
    confidence_var = rx.Var.create(rec["confidence_score"] * 100)
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    rec["recommendation_type"]
                    .to_string()
                    .replace("_", " ")
                    .capitalize(),
                    class_name=f"text-xs font-bold px-2 py-1 rounded-md {rec_type_colors.get(rec['recommendation_type'])}",
                ),
                rx.el.div(
                    rx.el.span(f"{confidence_var.to(int)}%", class_name="font-bold"),
                    rx.el.span("Confidence", class_name="text-xs text-gray-500"),
                    class_name="flex flex-col items-end",
                ),
                class_name="flex items-center justify-between mb-3",
            ),
            rx.el.p(rec["reasoning"], class_name="text-sm text-gray-600 mb-4"),
            rx.el.div(
                rx.el.h4(
                    "Predicted Impact",
                    class_name="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2",
                ),
                rx.el.div(
                    rx.foreach(
                        rec["impact_preview"].items(),
                        lambda item: rx.el.div(
                            rx.el.p(item[0], class_name="text-sm font-medium"),
                            rx.el.p(
                                item[1].to_string(), class_name="text-sm text-gray-500"
                            ),
                            class_name="text-right",
                        ),
                    ),
                    class_name="grid grid-cols-3 gap-4",
                ),
                class_name="p-3 bg-gray-50 rounded-md border",
            ),
            class_name="flex-grow",
        ),
        rx.el.div(
            rx.el.button(
                "Dismiss",
                on_click=lambda: RecommendationState.dismiss_recommendation(rec["id"]),
                class_name="text-sm text-gray-600 hover:text-gray-900 font-medium",
            ),
            rx.el.button(
                "Apply",
                on_click=lambda: RecommendationState.select_recommendation_for_apply(
                    rec["id"]
                ),
                class_name="text-sm bg-teal-500 text-white px-4 py-1.5 rounded-md font-semibold hover:bg-teal-600",
            ),
            class_name="flex items-center justify-end gap-4 mt-6 pt-4 border-t",
        ),
        class_name="bg-white p-6 rounded-lg shadow-sm border flex flex-col",
    )


def apply_modal() -> rx.Component:
    return rx.radix.primitives.dialog.root(
        rx.radix.primitives.dialog.content(
            rx.cond(
                RecommendationState.selected_recommendation,
                rx.fragment(
                    rx.radix.primitives.dialog.title(
                        f"Apply Recommendation: {RecommendationState.selected_recommendation['recommendation_type'].to_string().replace('_', ' ').capitalize()}",
                        class_name="text-2xl font-bold text-gray-800",
                    ),
                    rx.radix.primitives.dialog.description(
                        RecommendationState.selected_recommendation["reasoning"],
                        class_name="text-gray-600 mt-2 mb-6",
                    ),
                    rx.el.div(
                        rx.el.h4(
                            "Confirm Impact",
                            class_name="font-semibold text-gray-700 mb-2",
                        ),
                        rx.el.table(
                            rx.el.tbody(
                                rx.foreach(
                                    RecommendationState.selected_recommendation[
                                        "impact_preview"
                                    ].items(),
                                    lambda item: rx.el.tr(
                                        rx.el.td(item[0], class_name="font-medium"),
                                        rx.el.td(
                                            item[1].to_string(),
                                            class_name="text-right text-gray-700",
                                        ),
                                    ),
                                ),
                                class_name="divide-y divide-gray-200",
                            ),
                            class_name="w-full text-sm mb-6",
                        ),
                        class_name="p-4 bg-gray-50 rounded-lg border",
                    ),
                    rx.el.div(
                        rx.el.button(
                            "Cancel",
                            on_click=RecommendationState.close_apply_modal,
                            class_name="bg-gray-200 text-gray-800 px-4 py-2 rounded-md font-semibold hover:bg-gray-300",
                        ),
                        rx.el.div(
                            rx.el.button(
                                "Start A/B Test",
                                on_click=RecommendationState.start_ab_test,
                                class_name="bg-yellow-500 text-white px-4 py-2 rounded-md font-semibold hover:bg-yellow-600",
                            ),
                            rx.el.button(
                                "Apply Now",
                                on_click=RecommendationState.apply_recommendation,
                                is_loading=RecommendationState.is_loading,
                                class_name="bg-teal-500 text-white px-4 py-2 rounded-md font-semibold hover:bg-teal-600",
                            ),
                            class_name="flex gap-3",
                        ),
                        class_name="flex justify-between items-center mt-8",
                    ),
                ),
                rx.el.div("Loading recommendation..."),
            )
        ),
        open=RecommendationState.show_apply_modal,
        on_open_change=lambda is_open: rx.cond(
            is_open, rx.noop(), RecommendationState.close_apply_modal
        ),
    )


def recommendations_page() -> rx.Component:
    """The page for viewing and applying AI-powered recommendations."""
    return rx.el.div(
        rx.el.div(
            rx.el.h1(
                "Optimization Center", class_name="text-3xl font-bold text-gray-800"
            ),
            rx.el.p(
                "AI-powered recommendations to optimize your security posture and costs.",
                class_name="text-gray-600 mt-1",
            ),
            rx.el.button(
                rx.icon("refresh-cw", class_name="mr-2 h-4 w-4"),
                "Generate New Recommendations",
                on_click=RecommendationState.generate_recommendations,
                is_loading=RecommendationState.is_generating,
                class_name="bg-teal-400 text-white px-4 py-2 rounded-lg font-semibold hover:bg-teal-500 transition flex items-center",
            ),
            class_name="flex justify-between items-center mb-8",
        ),
        rx.cond(
            RecommendationState.is_generating
            & (RecommendationState.pending_recommendations.length() == 0),
            rx.el.div(
                rx.el.div(class_name="h-64 bg-gray-200 rounded-lg animate-pulse"),
                rx.el.div(class_name="h-64 bg-gray-200 rounded-lg animate-pulse"),
                class_name="grid grid-cols-1 lg:grid-cols-2 gap-8",
            ),
            rx.cond(
                RecommendationState.pending_recommendations.length() > 0,
                rx.el.div(
                    rx.foreach(
                        RecommendationState.pending_recommendations, recommendation_card
                    ),
                    class_name="grid grid-cols-1 lg:grid-cols-2 gap-8",
                ),
                rx.el.div(
                    rx.icon(
                        "square_check", class_name="mx-auto h-16 w-16 text-green-500"
                    ),
                    rx.el.h3(
                        "You're all optimized!",
                        class_name="mt-4 text-xl font-semibold text-gray-900",
                    ),
                    rx.el.p(
                        "There are no new recommendations at this time. Check back later.",
                        class_name="mt-1 text-sm text-gray-500",
                    ),
                    class_name="text-center py-24 border-2 border-dashed rounded-lg bg-gray-50",
                ),
            ),
        ),
        apply_modal(),
        class_name="p-8",
        on_mount=RecommendationState.generate_recommendations,
    )