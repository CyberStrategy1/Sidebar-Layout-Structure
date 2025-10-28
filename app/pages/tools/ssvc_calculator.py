import reflex as rx
from app.components.tools_layout import tools_layout
from app.states.ssvc_calculator_state import SsvcCalculatorState, QUESTIONS


def progress_indicator() -> rx.Component:
    """A visual progress bar for the SSVC decision tree steps."""
    return rx.el.div(
        rx.foreach(
            list(QUESTIONS.keys()),
            lambda item, index: rx.el.div(
                rx.el.div(
                    rx.el.div(
                        rx.cond(
                            SsvcCalculatorState.current_step > index,
                            rx.icon("check", class_name="h-5 w-5 text-white"),
                            rx.el.span(index + 1),
                        ),
                        class_name=rx.cond(
                            SsvcCalculatorState.current_step > index,
                            "flex h-8 w-8 items-center justify-center rounded-full bg-teal-500 text-white font-semibold",
                            rx.cond(
                                SsvcCalculatorState.current_step == index,
                                "flex h-8 w-8 items-center justify-center rounded-full border-2 border-teal-500 bg-gray-800 text-teal-400 font-semibold",
                                "flex h-8 w-8 items-center justify-center rounded-full border-2 border-gray-600 bg-gray-800 text-gray-400 font-semibold",
                            ),
                        ),
                    ),
                    class_name="relative",
                ),
                rx.el.p(
                    item.replace("_", " ").capitalize(),
                    class_name=rx.cond(
                        SsvcCalculatorState.current_step >= index,
                        "mt-2 text-sm font-medium text-white text-center",
                        "mt-2 text-sm font-medium text-gray-500 text-center",
                    ),
                ),
                class_name="flex flex-col items-center",
            ),
        ),
        class_name="flex justify-between w-full max-w-4xl mx-auto mb-16",
    )


def question_card() -> rx.Component:
    """Displays the current question and answer options."""
    return rx.el.div(
        rx.el.button(
            rx.icon("arrow-left", class_name="mr-2 h-4 w-4"),
            "Back",
            on_click=lambda: SsvcCalculatorState.go_to_step(
                SsvcCalculatorState.current_step - 1
            ),
            class_name="absolute top-0 left-0 text-gray-400 hover:text-white transition-colors flex items-center",
            disabled=SsvcCalculatorState.current_step == 0,
        ),
        rx.el.h2(
            SsvcCalculatorState.active_question["text"],
            class_name="text-2xl md:text-3xl font-bold text-center text-white mb-8",
        ),
        rx.el.div(
            rx.foreach(
                SsvcCalculatorState.active_question["options"],
                lambda option: rx.el.button(
                    option["label"],
                    on_click=lambda: SsvcCalculatorState.select_answer(option["value"]),
                    class_name="w-full p-4 text-lg font-semibold rounded-lg bg-gray-800 hover:bg-teal-500/20 border-2 border-gray-700 hover:border-teal-500 transition text-white text-center",
                ),
            ),
            class_name="grid grid-cols-1 md:grid-cols-3 gap-4",
        ),
        class_name="w-full max-w-3xl relative",
    )


def result_card() -> rx.Component:
    """Displays the final SSVC decision and rationale."""
    return rx.el.div(
        rx.el.div(
            rx.el.h2(
                "Your SSVC Decision is:", class_name="text-2xl font-bold text-white"
            ),
            rx.el.div(
                SsvcCalculatorState.decision.capitalize(),
                class_name="text-7xl font-bold tracking-tighter "
                + SsvcCalculatorState.decision_colors[
                    SsvcCalculatorState.decision
                ].to_string(),
            ),
            class_name="text-center mb-8",
        ),
        rx.el.div(
            rx.el.h3("Decision Rationale", class_name="font-semibold text-white mb-2"),
            rx.el.p(SsvcCalculatorState.decision_rationale, class_name="text-gray-300"),
            class_name="bg-gray-800/50 p-6 rounded-lg border border-gray-700 mb-8 text-center",
        ),
        rx.el.div(
            rx.el.button(
                "Start Over",
                on_click=SsvcCalculatorState.reset_calculator,
                class_name="bg-gray-600 text-white px-6 py-2 rounded-lg font-semibold hover:bg-gray-500 transition",
            ),
            rx.el.a(
                rx.el.button(
                    "Sign Up to Save & Export",
                    class_name="bg-teal-500 text-white px-6 py-2 rounded-lg font-semibold hover:bg-teal-600 transition",
                ),
                href="/register",
            ),
            class_name="flex justify-center gap-4",
        ),
        class_name="w-full max-w-2xl",
    )


def ssvc_calculator_page() -> rx.Component:
    """The SSVC Calculator tool page."""
    return tools_layout(
        rx.el.div(
            rx.el.div(
                rx.el.h1(
                    "SSVC Decision Tree Calculator",
                    class_name="text-4xl md:text-5xl font-bold tracking-tighter text-center bg-clip-text text-transparent bg-gradient-to-r from-teal-300 to-blue-400",
                ),
                rx.el.p(
                    "Use the Stakeholder-Specific Vulnerability Categorization (SSVC) framework to prioritize vulnerabilities based on impact.",
                    class_name="max-w-3xl mx-auto mt-4 text-center text-lg text-gray-300",
                ),
                class_name="py-16 md:py-24",
            ),
            rx.el.div(
                progress_indicator(),
                rx.cond(SsvcCalculatorState.decision, result_card(), question_card()),
                class_name="flex flex-col items-center px-4",
            ),
            class_name="container mx-auto px-4 md:px-6 py-12",
        )
    )