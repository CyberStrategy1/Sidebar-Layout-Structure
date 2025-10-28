import reflex as rx


def admin_sidebar() -> rx.Component:
    """The sidebar component for admin console navigation."""
    return rx.el.aside(
        rx.el.div(
            rx.el.div(
                rx.el.a(
                    rx.icon("shield-alert", class_name="h-8 w-8 text-red-400"),
                    href="/admin",
                    class_name="flex items-center gap-2 font-semibold text-white",
                ),
                rx.el.h1("Admin Console", class_name="text-xl font-bold text-white"),
                class_name="flex h-16 items-center gap-4 border-b border-gray-600 px-6",
            ),
            rx.el.nav(
                rx.el.div(
                    rx.el.h3(
                        "Analytics",
                        class_name="text-lg font-bold text-white px-4 pt-4 pb-2",
                    ),
                    rx.link(
                        "Customer Analytics",
                        href="/admin",
                        color="white",
                        class_name="block px-4 py-2 text-sm",
                    ),
                    rx.link(
                        "API Health",
                        href="/admin/api-health",
                        color="white",
                        class_name="block px-4 py-2 text-sm",
                    ),
                ),
                class_name="flex flex-col gap-1 p-4",
            ),
        ),
        class_name="fixed left-0 top-0 z-10 h-screen w-[250px] bg-[#2E3A4D] font-['Montserrat'] border-r border-gray-700",
    )