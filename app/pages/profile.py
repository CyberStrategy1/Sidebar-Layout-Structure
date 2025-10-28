import reflex as rx


def profile_page() -> rx.Component:
    """The profile page content."""
    return rx.el.div(
        rx.el.h1("User Profile", class_name="text-3xl font-bold text-gray-800 mb-6"),
        rx.el.p(
            "This is the user profile page. User details and account information will be managed here.",
            class_name="text-gray-600",
        ),
        class_name="p-8",
    )