import reflex as rx
from app.states.tools_layout_state import ToolsLayoutState

TOOL_LIST = [
    {
        "name": "Framework Comparison",
        "href": "/tools/framework-comparison",
        "description": "Compare a CVE across 11+ frameworks side-by-side.",
    },
    {
        "name": "SSVC Calculator",
        "href": "/tools/ssvc-calculator",
        "description": "Determine vulnerability priority with a decision tree.",
    },
    {
        "name": "KEV Checker",
        "href": "/tools/kev-checker",
        "description": "Check if a CVE is in CISA's KEV catalog.",
    },
    {
        "name": "EPSS Tracker",
        "href": "/tools/epss-tracker",
        "description": "Track exploitation probability over time.",
    },
    {
        "name": "CVSS Calculator",
        "href": "/tools/cvss-calculator",
        "description": "Calculate and visualize CVSS 3.1 scores.",
    },
    {
        "name": "VEX Validator",
        "href": "/tools/vex-validator",
        "description": "Validate and analyze VEX documents.",
    },
    {
        "name": "Microsoft CVE Intelligence",
        "href": "/tools/microsoft-cve",
        "description": "Search Microsoft-specific vulnerability data.",
    },
]


def tools_header() -> rx.Component:
    return rx.el.header(
        rx.el.div(
            rx.el.a(
                rx.icon("command", class_name="h-8 w-8 text-teal-400"),
                href="/",
                class_name="flex items-center gap-2 font-semibold text-white",
            ),
            rx.el.nav(
                rx.el.a(
                    "All Tools",
                    href="/tools",
                    class_name="text-gray-300 hover:text-white transition-colors",
                ),
                rx.el.a(
                    "Pricing",
                    href="/pricing",
                    class_name="text-gray-300 hover:text-white transition-colors",
                ),
                class_name="hidden md:flex items-center gap-6 text-sm font-medium",
            ),
            rx.el.div(
                rx.el.a(
                    rx.el.button(
                        "Sign In",
                        class_name="text-white font-semibold hover:bg-gray-700 px-4 py-2 rounded-md transition",
                    ),
                    href="/login",
                ),
                rx.el.a(
                    rx.el.button(
                        "Sign Up",
                        class_name="bg-teal-400 text-white font-semibold px-4 py-2 rounded-md hover:bg-teal-500 transition",
                    ),
                    href="/register",
                ),
                class_name="flex items-center gap-2",
            ),
            class_name="container mx-auto flex h-16 items-center justify-between px-4 md:px-6",
        ),
        class_name="sticky top-0 z-50 w-full border-b border-gray-700 bg-[#2E3A4D]/80 backdrop-blur-sm",
    )


def tools_footer() -> rx.Component:
    return rx.el.footer(
        rx.el.div(
            rx.el.div(
                rx.el.a(
                    rx.icon("command", class_name="h-8 w-8 text-teal-400"), href="/"
                ),
                rx.el.p(
                    "Aperture Enterprise © 2024", class_name="text-sm text-gray-400"
                ),
                class_name="flex items-center gap-4",
            ),
            rx.el.nav(
                rx.foreach(
                    TOOL_LIST,
                    lambda tool: rx.el.a(
                        tool["name"],
                        href=tool["href"],
                        class_name="text-sm font-medium text-gray-300 hover:text-white transition-colors",
                    ),
                ),
                class_name="hidden md:flex flex-wrap items-center justify-center gap-x-6 gap-y-2",
            ),
            class_name="container mx-auto flex flex-col md:flex-row items-center justify-between gap-4 px-4 py-6 md:px-6",
        ),
        class_name="bg-[#2E3A4D] border-t border-gray-700",
    )


def tools_layout(content: rx.Component) -> rx.Component:
    """The layout for all free tool pages."""
    return rx.el.div(
        tools_header(),
        rx.el.main(content, class_name="flex-1"),
        tools_footer(),
        class_name="flex flex-col min-h-screen bg-gray-900 text-white font-['Montserrat']",
    )