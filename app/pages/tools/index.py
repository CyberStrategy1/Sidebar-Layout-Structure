import reflex as rx
from app.states.tools_index_state import ToolsIndexState
from app.components.tools_layout import tools_layout, TOOL_LIST


def tool_card(tool: dict) -> rx.Component:
    return rx.el.a(
        rx.el.div(
            rx.el.h3(tool["name"], class_name="text-xl font-bold text-white mb-2"),
            rx.el.p(tool["description"], class_name="text-gray-400 text-sm"),
            class_name="flex-grow",
        ),
        rx.el.div(
            "Try Now",
            rx.icon("arrow-right", class_name="ml-2 h-4 w-4"),
            class_name="mt-4 flex items-center text-teal-400 font-semibold",
        ),
        href=tool["href"],
        class_name="bg-gray-800/50 p-6 rounded-lg border border-gray-700 hover:border-teal-400 hover:bg-gray-800 transition flex flex-col h-full",
    )


def tools_index_page() -> rx.Component:
    """The main landing page for all free tools."""
    return tools_layout(
        rx.el.div(
            rx.el.div(
                rx.el.h1(
                    "Free Vulnerability Intelligence Tools",
                    class_name="text-4xl md:text-5xl font-bold tracking-tighter text-center bg-clip-text text-transparent bg-gradient-to-r from-teal-300 to-blue-400",
                ),
                rx.el.p(
                    "A suite of powerful, free tools to help you prioritize vulnerabilities, analyze threats, and secure your stack.",
                    class_name="max-w-3xl mx-auto mt-4 text-center text-lg text-gray-300",
                ),
                class_name="py-20 md:py-28",
            ),
            rx.el.div(
                rx.foreach(TOOL_LIST, tool_card),
                class_name="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8",
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.h2(
                        "Ready to Supercharge Your Security?",
                        class_name="text-3xl font-bold text-white",
                    ),
                    rx.el.p(
                        "Sign up for Aperture to save your work, set up alerts, and integrate with your full tech stack.",
                        class_name="text-gray-300 mt-2 max-w-xl",
                    ),
                ),
                rx.el.a(
                    rx.el.button(
                        "Create Your Free Account",
                        class_name="bg-teal-400 text-white font-semibold px-6 py-3 rounded-lg hover:bg-teal-500 transition-transform duration-200 transform hover:scale-105",
                    ),
                    href="/register",
                ),
                class_name="mt-24 mb-16 flex flex-col md:flex-row items-center justify-between gap-8 bg-gray-800 p-8 rounded-2xl",
            ),
            class_name="container mx-auto px-4 md:px-6",
        )
    )