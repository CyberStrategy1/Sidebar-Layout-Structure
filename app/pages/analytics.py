import reflex as rx


def analytics_page() -> rx.Component:
    """The analytics page content."""
    return rx.el.div(
        rx.el.h1("Analytics", class_name="text-3xl font-bold text-gray-800 mb-6"),
        rx.el.p(
            "This is the analytics page. Detailed charts and data visualizations will be displayed here.",
            class_name="text-gray-600",
        ),
        class_name="p-8",
    )