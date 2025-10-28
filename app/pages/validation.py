import reflex as rx
from app.states.validation_state import (
    ValidationState,
    FrameworkPerformance,
    ValidationRecord,
    AutoTuneEvent,
)


def accuracy_gauge(value: rx.Var[float]) -> rx.Component:
    color_class = rx.cond(
        value > 90,
        "text-teal-500",
        rx.cond(value > 80, "text-yellow-500", "text-red-500"),
    )
    return rx.el.div(
        rx.el.p(
            "Overall Model Accuracy", class_name="text-lg font-medium text-gray-700"
        ),
        rx.el.div(
            rx.el.span(f"{value.to_string()}%", class_name="text-7xl font-bold"),
            class_name=f"mt-2 {color_class}",
        ),
        class_name="text-center bg-white p-6 rounded-lg shadow-sm border",
    )


def performance_trends_chart() -> rx.Component:
    return rx.el.div(
        rx.el.h3(
            "Accuracy Over Time (30 Days)",
            class_name="text-lg font-semibold text-gray-800 mb-4",
        ),
        rx.recharts.area_chart(
            rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
            rx.recharts.graphing_tooltip(
                content_style={
                    "background": "white",
                    "border": "1px solid #ccc",
                    "borderRadius": "0.5rem",
                }
            ),
            rx.recharts.x_axis(data_key="date"),
            rx.recharts.y_axis(domain=[80, 100], unit="%"),
            rx.recharts.area(
                type="monotone",
                data_key="accuracy",
                stroke="#14b8a6",
                fill="#14b8a6",
                fill_opacity=0.3,
            ),
            data=ValidationState.accuracy_trend,
            height=300,
        ),
        class_name="bg-white p-6 rounded-lg shadow-sm border lg:col-span-2",
    )


def framework_comparison_matrix() -> rx.Component:
    def row(item: FrameworkPerformance) -> rx.Component:
        accuracy_val = item["accuracy"] * 100
        return rx.el.tr(
            rx.el.td(item["framework"], class_name="px-4 py-3 font-semibold"),
            rx.el.td(
                rx.el.span(
                    f"{str(accuracy_val)}%",
                    class_name=rx.cond(
                        accuracy_val < 85, "text-red-500 font-bold", "text-gray-700"
                    ),
                ),
                class_name="px-4 py-3 text-center",
            ),
            rx.el.td(
                f"{str(item['precision'] * 100)}%", class_name="px-4 py-3 text-center"
            ),
            rx.el.td(
                f"{str(item['recall'] * 100)}%", class_name="px-4 py-3 text-center"
            ),
            rx.el.td(
                f"{str(item['f1_score'] * 100)}%", class_name="px-4 py-3 text-center"
            ),
            class_name="border-b hover:bg-gray-50",
        )

    return rx.el.div(
        rx.el.h3(
            "Framework Performance Matrix",
            class_name="text-lg font-semibold text-gray-800 mb-4",
        ),
        rx.el.table(
            rx.el.thead(
                rx.el.tr(
                    rx.el.th("Framework", class_name="px-4 py-2 text-left"),
                    rx.el.th("Accuracy", class_name="px-4 py-2 text-center"),
                    rx.el.th("Precision", class_name="px-4 py-2 text-center"),
                    rx.el.th("Recall", class_name="px-4 py-2 text-center"),
                    rx.el.th("F1-Score", class_name="px-4 py-2 text-center"),
                )
            ),
            rx.el.tbody(rx.foreach(ValidationState.performance_metrics, row)),
            class_name="w-full text-sm",
        ),
        class_name="bg-white p-6 rounded-lg shadow-sm border",
    )


def error_log_viewer() -> rx.Component:
    def row(item: ValidationRecord) -> rx.Component:
        return rx.el.tr(
            rx.el.td(item["cve_id"], class_name="px-4 py-3 font-mono"),
            rx.el.td(item["framework"], class_name="px-4 py-3"),
            rx.el.td(item["predicted_score"], class_name="px-4 py-3 text-center"),
            rx.el.td(
                item["ground_truth_score"],
                class_name="px-4 py-3 text-center text-green-600 font-semibold",
            ),
            rx.el.td(
                item["error_margin"],
                class_name="px-4 py-3 text-center text-red-600 font-bold",
            ),
            rx.el.td(item["validated_at"].split("T")[0], class_name="px-4 py-3"),
            class_name="border-b",
        )

    return rx.el.div(
        rx.el.h3(
            "Validation Error Log",
            class_name="text-lg font-semibold text-gray-800 mb-4",
        ),
        rx.data_table(
            data=ValidationState.error_logs,
            columns=[
                {"title": "CVE ID", "type": "str"},
                {"title": "Framework", "type": "str"},
                {"title": "Predicted", "type": "number"},
                {"title": "Actual", "type": "number"},
                {"title": "Error Margin", "type": "number"},
                {"title": "Timestamp", "type": "str"},
            ],
            pagination=True,
            search=True,
            sort=True,
        ),
        class_name="bg-white p-6 rounded-lg shadow-sm border mt-8",
    )


def tuning_panel() -> rx.Component:
    return rx.el.div(
        rx.el.h3(
            "Automated Tuning Engine",
            class_name="text-lg font-semibold text-gray-800 mb-4",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.p("Auto-Tuning Status", class_name="font-medium"),
                rx.el.p(
                    "System automatically adjusts weights when accuracy drops.",
                    class_name="text-xs text-gray-500",
                ),
            ),
            rx.switch(
                checked=ValidationState.auto_tuning_enabled,
                on_change=ValidationState.toggle_auto_tuning,
            ),
            class_name="flex justify-between items-center bg-gray-50 p-4 rounded-lg border mb-4",
        ),
        rx.el.h4("Tuning History", class_name="font-semibold mb-2"),
        rx.el.div(
            rx.el.table(
                rx.el.thead(
                    rx.el.tr(
                        rx.el.th("Timestamp", class_name="px-2 py-1 text-left text-xs"),
                        rx.el.th("Framework", class_name="px-2 py-1 text-left text-xs"),
                        rx.el.th("Reason", class_name="px-2 py-1 text-left text-xs"),
                    )
                ),
                rx.el.tbody(
                    rx.foreach(
                        ValidationState.tuning_history,
                        lambda event: rx.el.tr(
                            rx.el.td(
                                event["timestamp"].split("T")[0],
                                class_name="px-2 py-1 text-xs",
                            ),
                            rx.el.td(
                                event["framework"], class_name="px-2 py-1 text-xs"
                            ),
                            rx.el.td(event["reason"], class_name="px-2 py-1 text-xs"),
                            class_name="border-b",
                        ),
                    )
                ),
                class_name="w-full text-sm",
            ),
            class_name="max-h-48 overflow-y-auto",
        ),
        class_name="bg-white p-6 rounded-lg shadow-sm border",
    )


def tuning_panel() -> rx.Component:
    return rx.el.div(
        rx.el.h3(
            "Automated Tuning Engine",
            class_name="text-lg font-semibold text-gray-800 mb-4",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.p("Auto-Tuning Status", class_name="font-medium"),
                rx.el.p(
                    "System automatically adjusts weights when accuracy drops.",
                    class_name="text-xs text-gray-500",
                ),
            ),
            rx.switch(
                checked=ValidationState.auto_tuning_enabled,
                on_change=ValidationState.toggle_auto_tuning,
            ),
            class_name="flex justify-between items-center bg-gray-50 p-4 rounded-lg border mb-4",
        ),
        rx.el.h4("Tuning History", class_name="font-semibold mb-2"),
        rx.el.div(
            rx.el.table(
                rx.el.thead(
                    rx.el.tr(
                        rx.el.th("Timestamp", class_name="px-2 py-1 text-left text-xs"),
                        rx.el.th("Framework", class_name="px-2 py-1 text-left text-xs"),
                        rx.el.th("Reason", class_name="px-2 py-1 text-left text-xs"),
                    )
                ),
                rx.el.tbody(
                    rx.foreach(
                        ValidationState.tuning_history,
                        lambda event: rx.el.tr(
                            rx.el.td(
                                event["timestamp"].split("T")[0],
                                class_name="px-2 py-1 text-xs",
                            ),
                            rx.el.td(
                                event["framework"], class_name="px-2 py-1 text-xs"
                            ),
                            rx.el.td(event["reason"], class_name="px-2 py-1 text-xs"),
                            class_name="border-b",
                        ),
                    )
                ),
                class_name="w-full text-sm",
            ),
            class_name="max-h-48 overflow-y-auto",
        ),
        class_name="bg-white p-6 rounded-lg shadow-sm border",
    )


def framework_comparison_matrix() -> rx.Component:
    def row(item: FrameworkPerformance) -> rx.Component:
        accuracy_val = item["accuracy"] * 100
        return rx.el.tr(
            rx.el.td(item["framework"], class_name="px-4 py-3 font-semibold"),
            rx.el.td(
                rx.el.span(
                    f"{str(accuracy_val)}%",
                    class_name=rx.cond(
                        accuracy_val < 85, "text-red-500 font-bold", "text-gray-700"
                    ),
                ),
                class_name="px-4 py-3 text-center",
            ),
            rx.el.td(
                f"{str(item['precision'] * 100)}%", class_name="px-4 py-3 text-center"
            ),
            rx.el.td(
                f"{str(item['recall'] * 100)}%", class_name="px-4 py-3 text-center"
            ),
            rx.el.td(
                f"{str(item['f1_score'] * 100)}%", class_name="px-4 py-3 text-center"
            ),
            class_name="border-b hover:bg-gray-50",
        )

    return rx.el.div(
        rx.el.h3(
            "Framework Performance Matrix",
            class_name="text-lg font-semibold text-gray-800 mb-4",
        ),
        rx.el.table(
            rx.el.thead(
                rx.el.tr(
                    rx.el.th("Framework", class_name="px-4 py-2 text-left"),
                    rx.el.th("Accuracy", class_name="px-4 py-2 text-center"),
                    rx.el.th("Precision", class_name="px-4 py-2 text-center"),
                    rx.el.th("Recall", class_name="px-4 py-2 text-center"),
                    rx.el.th("F1-Score", class_name="px-4 py-2 text-center"),
                )
            ),
            rx.el.tbody(rx.foreach(ValidationState.performance_metrics, row)),
            class_name="w-full text-sm",
        ),
        class_name="bg-white p-6 rounded-lg shadow-sm border",
    )


def error_log_viewer() -> rx.Component:
    def row(item: ValidationRecord) -> rx.Component:
        return rx.el.tr(
            rx.el.td(item["cve_id"], class_name="px-4 py-3 font-mono"),
            rx.el.td(item["framework"], class_name="px-4 py-3"),
            rx.el.td(item["predicted_score"], class_name="px-4 py-3 text-center"),
            rx.el.td(
                item["ground_truth_score"],
                class_name="px-4 py-3 text-center text-green-600 font-semibold",
            ),
            rx.el.td(
                item["error_margin"],
                class_name="px-4 py-3 text-center text-red-600 font-bold",
            ),
            rx.el.td(item["validated_at"].split("T")[0], class_name="px-4 py-3"),
            class_name="border-b",
        )

    return rx.el.div(
        rx.el.h3(
            "Validation Error Log",
            class_name="text-lg font-semibold text-gray-800 mb-4",
        ),
        rx.data_table(
            data=ValidationState.error_logs,
            columns=[
                {"title": "CVE ID", "type": "str"},
                {"title": "Framework", "type": "str"},
                {"title": "Predicted", "type": "number"},
                {"title": "Actual", "type": "number"},
                {"title": "Error Margin", "type": "number"},
                {"title": "Timestamp", "type": "str"},
            ],
            pagination=True,
            search=True,
            sort=True,
        ),
        class_name="bg-white p-6 rounded-lg shadow-sm border mt-8",
    )


def tuning_panel() -> rx.Component:
    return rx.el.div(
        rx.el.h3(
            "Automated Tuning Engine",
            class_name="text-lg font-semibold text-gray-800 mb-4",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.p("Auto-Tuning Status", class_name="font-medium"),
                rx.el.p(
                    "System automatically adjusts weights when accuracy drops.",
                    class_name="text-xs text-gray-500",
                ),
            ),
            rx.switch(
                checked=ValidationState.auto_tuning_enabled,
                on_change=ValidationState.toggle_auto_tuning,
            ),
            class_name="flex justify-between items-center bg-gray-50 p-4 rounded-lg border mb-4",
        ),
        rx.el.h4("Tuning History", class_name="font-semibold mb-2"),
        rx.el.div(
            rx.el.table(
                rx.el.thead(
                    rx.el.tr(
                        rx.el.th("Timestamp", class_name="px-2 py-1 text-left text-xs"),
                        rx.el.th("Framework", class_name="px-2 py-1 text-left text-xs"),
                        rx.el.th("Reason", class_name="px-2 py-1 text-left text-xs"),
                    )
                ),
                rx.el.tbody(
                    rx.foreach(
                        ValidationState.tuning_history,
                        lambda event: rx.el.tr(
                            rx.el.td(
                                event["timestamp"].split("T")[0],
                                class_name="px-2 py-1 text-xs",
                            ),
                            rx.el.td(
                                event["framework"], class_name="px-2 py-1 text-xs"
                            ),
                            rx.el.td(event["reason"], class_name="px-2 py-1 text-xs"),
                            class_name="border-b",
                        ),
                    )
                ),
                class_name="w-full text-sm",
            ),
            class_name="max-h-48 overflow-y-auto",
        ),
        class_name="bg-white p-6 rounded-lg shadow-sm border",
    )


def validation_page() -> rx.Component:
    """The Evidence-Based Validation & Tuning dashboard page."""
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.h1(
                    "Validation & Tuning Hub",
                    class_name="text-3xl font-bold text-gray-800",
                ),
                rx.el.p(
                    "Monitor and improve the accuracy of the risk scoring engine.",
                    class_name="text-gray-600 mt-1",
                ),
            ),
            rx.el.div(
                rx.el.p(
                    f"Last Run: {ValidationState.last_run_time}",
                    class_name="text-sm text-gray-500",
                ),
                rx.el.button(
                    "Run Validation",
                    on_click=ValidationState.load_validation_data,
                    is_loading=ValidationState.is_loading,
                    class_name="bg-teal-400 text-white px-4 py-2 rounded-lg font-semibold hover:bg-teal-500 transition",
                ),
                class_name="flex items-center gap-4",
            ),
            class_name="flex justify-between items-center mb-8",
        ),
        rx.cond(
            ValidationState.is_loading
            & (ValidationState.validation_history.length() == 0),
            rx.el.div(
                rx.spinner(class_name="h-12 w-12 text-teal-500"),
                rx.el.p(
                    "Initializing validation engine...", class_name="mt-4 text-gray-600"
                ),
                class_name="flex flex-col items-center justify-center h-96 border rounded-lg bg-gray-50",
            ),
            rx.fragment(
                rx.el.div(
                    accuracy_gauge(ValidationState.overall_accuracy),
                    performance_trends_chart(),
                    tuning_panel(),
                    class_name="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8",
                ),
                framework_comparison_matrix(),
                error_log_viewer(),
            ),
        ),
        class_name="p-8",
        on_mount=ValidationState.load_validation_data,
    )