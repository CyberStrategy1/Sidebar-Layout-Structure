import reflex as rx
from app.state import AppState
from app.components.upgrade_prompts import enterprise_badge, pro_badge, locked_feature


def settings_section(
    title: str, description: str, badge: rx.Component | None, content: rx.Component
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.h3(
                    title,
                    badge,
                    class_name="text-lg font-semibold text-gray-900 flex items-center",
                ),
                rx.el.p(description, class_name="mt-1 text-sm text-gray-600"),
            ),
            class_name="md:col-span-1",
        ),
        rx.el.div(content, class_name="md:col-span-2"),
        class_name="md:grid md:grid-cols-3 md:gap-6 bg-white p-6 rounded-lg shadow-sm border",
    )


def locked_placeholder(feature_name: str, required_tier: str) -> rx.Component:
    return rx.el.div(
        rx.el.p(
            f"The {feature_name} feature is available on the {required_tier.capitalize()} plan.",
            class_name="text-sm text-gray-600 mb-4",
        ),
        locked_feature(feature_name=feature_name, required_tier=required_tier),
        class_name="flex flex-col items-start p-6 border-2 border-dashed rounded-lg text-center",
    )


def settings_page() -> rx.Component:
    """The settings page content."""
    return rx.el.div(
        rx.el.h1("Settings", class_name="text-3xl font-bold text-gray-800 mb-6"),
        rx.el.div(
            settings_section(
                title="Single Sign-On (SSO)",
                description="Integrate with your identity provider for seamless access.",
                badge=enterprise_badge(),
                content=rx.cond(
                    AppState.can_use_sso,
                    rx.el.div(
                        rx.el.button(
                            "Configure SAML/OIDC",
                            class_name="bg-teal-500 text-white px-4 py-2 rounded-lg font-semibold hover:bg-teal-600 transition",
                        )
                    ),
                    locked_placeholder(
                        feature_name="SSO/SAML", required_tier="enterprise"
                    ),
                ),
            ),
            settings_section(
                title="AI Analysis Configuration",
                description="Customize the AI models and prompts used for vulnerability analysis.",
                badge=pro_badge(),
                content=rx.cond(
                    AppState.can_use_ai_analysis,
                    rx.el.a(
                        rx.el.button(
                            "Configure AI Providers",
                            class_name="bg-teal-500 text-white px-4 py-2 rounded-lg font-semibold hover:bg-teal-600 transition",
                        ),
                        href="/ai-config",
                    ),
                    locked_placeholder(feature_name="AI Analysis", required_tier="pro"),
                ),
            ),
            class_name="space-y-8",
        ),
        class_name="p-8",
    )