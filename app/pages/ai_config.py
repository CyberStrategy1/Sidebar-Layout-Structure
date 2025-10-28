import reflex as rx
from app.states.llm_analysis_state import LlmAnalysisState, PROVIDER_CONFIG
from app.states.credit_state import CreditState, CREDIT_PACKAGES


def api_key_input(provider: str) -> rx.Component:
    return rx.el.div(
        rx.el.label(f"{provider.capitalize()} API Key", class_name="font-medium"),
        rx.el.div(
            rx.el.input(
                type="password",
                placeholder="Enter your API key",
                on_change=lambda val: LlmAnalysisState.handle_api_key_change(
                    provider, val
                ),
                default_value=LlmAnalysisState.provider_keys.get(provider, ""),
                class_name="flex-grow border-r-0 rounded-l-md",
            ),
            rx.el.button(
                "Save",
                on_click=lambda: LlmAnalysisState.save_api_key(
                    provider, LlmAnalysisState.provider_keys.get(provider, "")
                ),
                class_name="bg-gray-200 hover:bg-gray-300 px-4 rounded-r-md font-semibold",
            ),
            class_name="flex mt-1",
        ),
        class_name="w-full",
    )


def provider_card(provider: str, details: dict) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h3(provider.capitalize(), class_name="text-xl font-bold"),
            rx.el.span(
                f"{details['cost_credits']} credits / analysis",
                class_name="text-sm text-gray-500",
            ),
            class_name="flex items-baseline justify-between",
        ),
        rx.el.p(f"Model: {details['model']}", class_name="text-sm text-gray-600 mt-2"),
        api_key_input(provider),
        rx.el.button(
            "Test Connection",
            on_click=lambda: LlmAnalysisState.test_api_key(provider),
            is_loading=LlmAnalysisState.test_connection_status.get(provider)
            == "testing",
            class_name="mt-2 text-sm text-teal-600 hover:underline",
        ),
        class_name="bg-white p-6 rounded-lg shadow-sm border",
    )


def credit_purchase_card(package_key: str, details: dict) -> rx.Component:
    return rx.el.div(
        rx.el.h3(details["name"], class_name="text-xl font-bold text-center"),
        rx.el.p(
            f"${details['price']}", class_name="text-4xl font-bold text-center my-4"
        ),
        rx.el.p(
            f"{details['credits']} AI Credits",
            class_name="text-center text-gray-600 mb-6",
        ),
        rx.el.button(
            "Purchase Now",
            on_click=lambda: CreditState.create_credit_checkout_session(package_key),
            is_loading=CreditState.is_loading
            & (CreditState.selected_package == package_key),
            class_name="w-full bg-teal-500 text-white py-2 rounded-md font-semibold hover:bg-teal-600 transition",
        ),
        class_name="bg-white p-8 rounded-lg shadow-sm border",
    )


def ai_config_page() -> rx.Component:
    """Page for configuring AI providers and managing credits."""
    return rx.el.div(
        rx.el.h1(
            "AI Analysis Configuration",
            class_name="text-3xl font-bold text-gray-800 mb-2",
        ),
        rx.el.p(
            "Manage your AI providers, API keys, and platform credits.",
            class_name="text-gray-600 mb-8",
        ),
        rx.el.div(
            rx.el.h2("Platform Credits", class_name="text-2xl font-bold mb-4"),
            rx.el.div(
                rx.el.p(
                    "Your Current Balance",
                    class_name="text-lg font-medium text-gray-700",
                ),
                rx.el.p(
                    f"{LlmAnalysisState.org_credits} Credits",
                    class_name="text-5xl font-bold text-teal-600",
                ),
                class_name="text-center",
            ),
            rx.el.div(
                rx.foreach(
                    list(CREDIT_PACKAGES.items()),
                    lambda item: credit_purchase_card(item[0], item[1]),
                ),
                class_name="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8",
            ),
            class_name="bg-gray-50 p-8 rounded-lg border mb-12",
        ),
        rx.el.div(
            rx.el.h2(
                "Bring Your Own Key (BYOK) Providers",
                class_name="text-2xl font-bold mb-4",
            ),
            rx.el.p(
                "Connect your own API keys for unlimited analysis at your provider's rates.",
                class_name="text-sm text-gray-500 mb-6",
            ),
            rx.el.div(
                rx.foreach(
                    list(PROVIDER_CONFIG.items()),
                    lambda item: provider_card(item[0], item[1]),
                ),
                class_name="grid grid-cols-1 lg:grid-cols-2 gap-8",
            ),
        ),
        class_name="p-8",
        on_mount=LlmAnalysisState.load_provider_keys,
    )