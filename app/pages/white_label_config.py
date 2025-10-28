import reflex as rx
from app.states.white_label_state import WhiteLabelState
from app.components.upgrade_prompts import enterprise_badge, locked_feature
from app.state import AppState


def config_input(
    label: str, placeholder: str, value: rx.Var[str], on_change
) -> rx.Component:
    return rx.el.div(
        rx.el.label(label, class_name="block text-sm font-medium text-gray-700"),
        rx.el.input(
            placeholder=placeholder,
            default_value=value,
            on_change=on_change,
            class_name="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-teal-500 focus:ring-teal-500 sm:text-sm",
        ),
        class_name="mb-4",
    )


def color_picker(label: str, value: rx.Var[str], on_change) -> rx.Component:
    return rx.el.div(
        rx.el.label(label, class_name="block text-sm font-medium text-gray-700"),
        rx.el.div(
            rx.el.input(
                type="color",
                default_value=value,
                on_change=on_change,
                class_name="h-10 w-10 p-1 border-gray-300 rounded-md cursor-pointer",
            ),
            rx.el.span(value, class_name="ml-3 font-mono text-sm"),
            class_name="flex items-center mt-1",
        ),
        class_name="mb-4",
    )


def live_preview_panel() -> rx.Component:
    return rx.el.div(
        rx.el.h3("Live Preview", class_name="text-lg font-bold text-gray-800 mb-4"),
        rx.el.div(
            rx.el.header(
                rx.el.div(
                    rx.el.a(
                        rx.el.image(src=WhiteLabelState.logo_url, class_name="h-8"),
                        href="/",
                    ),
                    rx.el.h1(
                        WhiteLabelState.company_name, class_name="text-xl font-bold"
                    ),
                    class_name="flex items-center gap-4",
                ),
                rx.el.button(
                    "Sample Button",
                    style={"backgroundColor": WhiteLabelState.accent_color},
                    class_name="text-white px-3 py-1.5 rounded-md text-sm font-semibold",
                ),
                class_name="flex h-16 items-center justify-between px-6 border-b",
                style={
                    "backgroundColor": WhiteLabelState.primary_color,
                    "color": "white",
                },
            ),
            rx.el.footer(
                rx.el.p(
                    WhiteLabelState.footer_text, class_name="text-sm text-gray-500"
                ),
                rx.el.div(
                    rx.el.a(
                        "Terms",
                        href=WhiteLabelState.terms_url,
                        class_name="text-sm hover:underline",
                    ),
                    rx.el.a(
                        "Privacy",
                        href=WhiteLabelState.privacy_url,
                        class_name="text-sm hover:underline",
                    ),
                    rx.el.a(
                        "Support",
                        href=WhiteLabelState.support_url,
                        class_name="text-sm hover:underline",
                    ),
                    class_name="flex items-center gap-4",
                ),
                class_name="flex items-center justify-between p-4 border-t mt-4",
            ),
            class_name="border rounded-lg p-4 bg-gray-50",
        ),
        class_name="sticky top-8",
    )


def white_label_config_page() -> rx.Component:
    """Page for configuring white-label settings."""
    return rx.el.div(
        rx.el.h1(
            "White-Label Configuration",
            class_name="text-3xl font-bold text-gray-800 mb-2",
        ),
        rx.el.p(
            "Customize the look and feel of the platform for your brand. This feature is available on the Enterprise plan.",
            class_name="text-gray-600 mb-8",
        ),
        rx.cond(
            AppState.active_org_plan == "enterprise",
            rx.el.div(
                rx.el.div(
                    rx.el.h2("Branding", class_name="text-xl font-bold mb-4"),
                    config_input(
                        "Company Name",
                        "Your Company LLC",
                        WhiteLabelState.company_name,
                        WhiteLabelState.set_company_name,
                    ),
                    config_input(
                        "Dashboard Title",
                        "My Custom Dashboard",
                        WhiteLabelState.dashboard_title,
                        WhiteLabelState.set_dashboard_title,
                    ),
                    config_input(
                        "Logo URL",
                        "https://your-cdn.com/logo.png",
                        WhiteLabelState.logo_url,
                        WhiteLabelState.set_logo_url,
                    ),
                    config_input(
                        "Favicon URL",
                        "/favicon.ico",
                        WhiteLabelState.favicon_url,
                        WhiteLabelState.set_favicon_url,
                    ),
                    rx.el.h2("Theming", class_name="text-xl font-bold mt-8 mb-4"),
                    rx.el.div(
                        color_picker(
                            "Primary Color",
                            WhiteLabelState.primary_color,
                            WhiteLabelState.set_primary_color,
                        ),
                        color_picker(
                            "Secondary Color",
                            WhiteLabelState.secondary_color,
                            WhiteLabelState.set_secondary_color,
                        ),
                        color_picker(
                            "Accent Color",
                            WhiteLabelState.accent_color,
                            WhiteLabelState.set_accent_color,
                        ),
                        class_name="grid grid-cols-2 lg:grid-cols-3 gap-8",
                    ),
                    rx.el.h2("Custom CSS", class_name="text-xl font-bold mt-8 mb-4"),
                    rx.el.textarea(
                        placeholder=".custom-class { color: red; }",
                        default_value=WhiteLabelState.custom_css,
                        on_change=WhiteLabelState.set_custom_css,
                        class_name="w-full p-2 border rounded-md font-mono text-sm h-32",
                    ),
                    rx.el.h2(
                        "Footer & Links", class_name="text-xl font-bold mt-8 mb-4"
                    ),
                    config_input(
                        "Footer Text",
                        "© 2024 Your Company",
                        WhiteLabelState.footer_text,
                        WhiteLabelState.set_footer_text,
                    ),
                    config_input(
                        "Support URL",
                        "/help",
                        WhiteLabelState.support_url,
                        WhiteLabelState.set_support_url,
                    ),
                    config_input(
                        "Terms of Service URL",
                        "/terms",
                        WhiteLabelState.terms_url,
                        WhiteLabelState.set_terms_url,
                    ),
                    config_input(
                        "Privacy Policy URL",
                        "/privacy",
                        WhiteLabelState.privacy_url,
                        WhiteLabelState.set_privacy_url,
                    ),
                    rx.el.h2("Domain", class_name="text-xl font-bold mt-8 mb-4"),
                    config_input(
                        "Custom Domain",
                        "app.yourcompany.com",
                        WhiteLabelState.custom_domain,
                        WhiteLabelState.set_custom_domain,
                    ),
                    rx.cond(
                        WhiteLabelState.error_message != "",
                        rx.el.div(
                            WhiteLabelState.error_message,
                            class_name="text-red-500 text-sm p-2 bg-red-50 rounded-md my-4",
                        ),
                        None,
                    ),
                    rx.el.div(
                        rx.el.button(
                            "Reset to Defaults",
                            on_click=WhiteLabelState.reset_to_defaults,
                            class_name="bg-gray-200 text-gray-700 px-4 py-2 rounded-md font-semibold hover:bg-gray-300 transition",
                        ),
                        rx.el.button(
                            "Save Configuration",
                            on_click=WhiteLabelState.save_white_label_config,
                            is_loading=WhiteLabelState.is_loading,
                            class_name="bg-teal-500 text-white px-4 py-2 rounded-md font-semibold hover:bg-teal-600 transition",
                        ),
                        class_name="flex justify-between items-center mt-8 pt-6 border-t",
                    ),
                    class_name="bg-white p-8 rounded-lg shadow-sm border col-span-2",
                ),
                rx.el.div(live_preview_panel(), class_name="col-span-1"),
                class_name="grid grid-cols-1 lg:grid-cols-3 gap-8",
            ),
            locked_feature(
                feature_name="White-Label Configuration", required_tier="enterprise"
            ),
        ),
        class_name="p-8",
        on_mount=WhiteLabelState.load_white_label_config,
    )