import reflex as rx
from app.state import AppState
from app.states.white_label_state import WhiteLabelState


def sidebar() -> rx.Component:
    """The sidebar component for navigation."""
    return rx.el.aside(
        rx.el.div(
            rx.el.div(
                rx.el.a(
                    rx.el.image(src=WhiteLabelState.logo_url, class_name="h-8 w-8"),
                    href="/",
                    class_name="flex items-center gap-2 font-semibold text-white",
                ),
                rx.el.h1(
                    WhiteLabelState.company_name,
                    class_name="text-xl font-bold text-white",
                ),
                class_name="flex h-16 items-center gap-4 border-b border-gray-600 px-6",
            ),
            rx.el.nav(
                rx.el.div(
                    rx.el.h3(
                        "Aperture",
                        class_name="text-lg font-bold text-white px-4 pt-4 pb-2",
                    ),
                    rx.link(
                        "Dashboard",
                        href="/",
                        color="white",
                        class_name="block px-4 py-2 text-sm",
                    ),
                    rx.link(
                        "My Tech Stack",
                        href="/tech_stack",
                        color="white",
                        class_name="block px-4 py-2 text-sm",
                    ),
                    rx.link(
                        "Reporting",
                        href="/reporting",
                        color="white",
                        class_name="block px-4 py-2 text-sm",
                    ),
                    rx.link(
                        "Analysis",
                        href="/analysis",
                        color="white",
                        class_name="block px-4 py-2 text-sm",
                    ),
                    rx.link(
                        "Billing",
                        href="/billing",
                        color="white",
                        class_name="block px-4 py-2 text-sm",
                    ),
                    rx.link(
                        "Gap Analysis",
                        href="/gap-analysis",
                        color="white",
                        class_name="block px-4 py-2 text-sm",
                    ),
                    rx.link(
                        "Backlog Dashboard",
                        href="/backlog-dashboard",
                        color="white",
                        class_name="block px-4 py-2 text-sm",
                    ),
                    rx.link(
                        "Risk Intelligence",
                        href="/risk-intelligence",
                        color="white",
                        class_name="block px-4 py-2 text-sm",
                    ),
                    rx.link(
                        "Framework Config",
                        href="/framework-config",
                        color="white",
                        class_name="block px-4 py-2 text-sm",
                    ),
                    rx.link(
                        "AI Analysis Config",
                        href="/ai-config",
                        color="white",
                        class_name="block px-4 py-2 text-sm",
                    ),
                    rx.link(
                        "Optimization Center",
                        href="/recommendations",
                        color="white",
                        class_name="block px-4 py-2 text-sm",
                    ),
                    rx.link(
                        "Validation Hub",
                        href="/validation",
                        color="white",
                        class_name="block px-4 py-2 text-sm",
                    ),
                    rx.link(
                        "White-Label Config",
                        href="/white-label-config",
                        color="white",
                        class_name="block px-4 py-2 text-sm",
                    ),
                    rx.link(
                        "API Configuration",
                        href="/api-config",
                        color="white",
                        class_name="block px-4 py-2 text-sm",
                    ),
                    rx.link(
                        "Exploit Intelligence",
                        href="/exploit-intelligence",
                        color="white",
                        class_name="block px-4 py-2 text-sm",
                    ),
                    rx.link(
                        "Runtime Correlation",
                        href="/integrations/runtime-correlation",
                        color="white",
                        class_name="block px-4 py-2 text-sm",
                    ),
                ),
                class_name="flex flex-col gap-1 p-4",
            ),
        ),
        class_name="fixed left-0 top-0 z-10 h-screen w-[250px] bg-[#2E3A4D] font-['Montserrat'] border-r border-gray-700",
    )