import reflex as rx
from app.states.inference_state import InferenceState


def inference_demo_page() -> rx.Component:
    """A simple UI to test and demonstrate the inference engine."""
    return rx.el.div(
        rx.el.h1(
            "AI Inference Engine Demo",
            class_name="text-3xl font-bold text-gray-800 mb-4",
        ),
        rx.el.p(
            "Enter a CVE ID to run the enrichment pipeline. This demonstrates the standalone ML model's capability.",
            class_name="text-gray-600 mb-6",
        ),
        rx.el.div(
            rx.el.input(
                placeholder="e.g., CVE-2024-21412",
                on_change=InferenceState.set_cve_id_input,
                default_value=InferenceState.cve_id_input,
                class_name="flex-grow p-2 border border-gray-300 rounded-l-md",
            ),
            rx.el.button(
                "Run Inference",
                on_click=InferenceState.run_inference,
                is_loading=InferenceState.is_inferring,
                class_name="bg-teal-500 text-white px-4 py-2 rounded-r-md font-semibold hover:bg-teal-600 transition",
            ),
            class_name="flex mb-6",
        ),
        rx.cond(
            InferenceState.is_inferring,
            rx.el.div(
                rx.spinner(class_name="h-12 w-12 text-teal-500"),
                rx.el.p(
                    "Running data loading, feature extraction, and model prediction...",
                    class_name="mt-4 text-gray-600",
                ),
                class_name="flex flex-col items-center justify-center h-64 border-2 border-dashed rounded-lg bg-gray-50",
            ),
            rx.cond(
                InferenceState.inference_result,
                rx.el.div(
                    rx.el.h3("Inference Output", class_name="text-xl font-bold mb-2"),
                    rx.el.pre(
                        rx.el.code(InferenceState.formatted_result),
                        class_name="bg-gray-900 text-white p-4 rounded-md text-sm overflow-x-auto",
                    ),
                    class_name="bg-white p-6 rounded-lg shadow-sm border",
                ),
                rx.el.div(
                    rx.icon(
                        "flask_conical", class_name="h-16 w-16 text-gray-400 mx-auto"
                    ),
                    rx.el.p(
                        "Output will appear here.",
                        class_name="text-center text-gray-500 mt-4",
                    ),
                    class_name="py-24 border-2 border-dashed rounded-lg",
                ),
            ),
        ),
        class_name="p-8",
    )