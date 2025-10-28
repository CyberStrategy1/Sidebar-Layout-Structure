import reflex as rx
from app.states.integration_state import IntegrationState
from app.components.upgrade_prompts import enterprise_badge, locked_feature
from app.state import AppState


def connection_status_indicator(status: rx.Var[str]) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            class_name=rx.cond(
                status == "success",
                "h-2 w-2 rounded-full bg-green-500",
                rx.cond(
                    status == "testing",
                    "h-2 w-2 rounded-full bg-yellow-500 animate-pulse",
                    rx.cond(
                        status == "failure",
                        "h-2 w-2 rounded-full bg-red-500",
                        "h-2 w-2 rounded-full bg-gray-400",
                    ),
                ),
            )
        ),
        rx.el.span(status.capitalize(), class_name="text-sm text-gray-600"),
        class_name="flex items-center gap-2",
    )


def integration_config_card(
    title: str,
    provider_options: list,
    state_provider: rx.Var[str],
    endpoint_var: rx.Var[str],
    api_key_var: rx.Var[str],
    on_save,
    on_test,
    is_saving: rx.Var[bool],
    connection_status: rx.Var[str],
) -> rx.Component:
    form_id = f"{title.lower()}-form"
    return rx.el.div(
        rx.el.h3(f"{title} Configuration", class_name="text-xl font-bold mb-4"),
        rx.el.form(
            rx.el.div(
                rx.el.label("Provider", class_name="font-medium"),
                rx.el.select(
                    rx.foreach(
                        provider_options,
                        lambda p: rx.el.option(p.capitalize(), value=p),
                    ),
                    name=f"{title.lower()}_provider",
                    default_value=state_provider,
                    class_name="w-full mt-1 p-2 border rounded-md",
                ),
                class_name="mb-4",
            ),
            rx.el.div(
                rx.el.label("API Endpoint", class_name="font-medium"),
                rx.el.input(
                    name=f"{title.lower()}_endpoint",
                    default_value=endpoint_var,
                    placeholder="https://api.yourprovider.com",
                    class_name="w-full mt-1 p-2 border rounded-md",
                ),
                class_name="mb-4",
            ),
            rx.el.div(
                rx.el.label("API Key", class_name="font-medium"),
                rx.el.input(
                    name=f"{title.lower()}_api_key",
                    default_value=api_key_var,
                    type="password",
                    class_name="w-full mt-1 p-2 border rounded-md",
                ),
                class_name="mb-4",
            ),
            rx.el.div(
                connection_status_indicator(connection_status),
                rx.el.div(
                    rx.el.button(
                        "Test Connection",
                        on_click=on_test,
                        type="button",
                        class_name="text-sm font-semibold text-teal-600 hover:underline",
                    ),
                    rx.el.button(
                        "Save",
                        type="submit",
                        is_loading=is_saving,
                        class_name="bg-teal-500 text-white px-4 py-2 rounded-md font-semibold hover:bg-teal-600",
                    ),
                    class_name="flex items-center gap-4",
                ),
                class_name="flex justify-between items-center mt-6",
            ),
            on_submit=on_save,
            id=form_id,
        ),
        class_name="bg-white p-6 rounded-lg shadow-sm border",
    )


def runtime_evidence_table() -> rx.Component:
    return rx.el.div(
        rx.el.h2(
            "Runtime Correlation Evidence",
            class_name="text-2xl font-bold text-gray-800 mb-4",
        ),
        rx.data_table(
            data=IntegrationState.correlation_results_list,
            columns=[
                {"title": "CVE ID", "type": "str", "key": "cve_id"},
                {"title": "Static Risk", "type": "number", "key": "static_risk_score"},
                {"title": "Runtime Confirmed", "type": "str"},
                {
                    "title": "True Risk Score",
                    "type": "number",
                    "key": "true_risk_score",
                },
                {"title": "Active Processes", "type": "str"},
                {"title": "Affected Endpoints", "type": "str"},
                {
                    "title": "Containment Priority",
                    "type": "str",
                    "key": "containment_priority",
                },
            ],
            pagination=True,
            search=True,
            sort=True,
        ),
        class_name="mt-8",
    )


def runtime_correlation_page() -> rx.Component:
    """Page for configuring SIEM/RMM integrations and viewing runtime evidence."""
    siem_providers = ["splunk", "sentinel", "stellar_cyber", "qradar", "hunters_ai"]
    rmm_providers = ["ninjaone", "datto", "connectwise", "manageengine", "pulseway"]
    return rx.el.div(
        rx.el.h1(
            "SIEM & RMM Integrations",
            class_name="text-3xl font-bold text-gray-800 mb-2",
        ),
        rx.el.p(
            "Connect your security tools to enable runtime vulnerability correlation.",
            class_name="text-gray-600 mb-8",
        ),
        rx.cond(
            AppState.can_use_sso,
            rx.el.div(
                integration_config_card(
                    "SIEM",
                    siem_providers,
                    IntegrationState.siem_provider,
                    IntegrationState.siem_endpoint,
                    IntegrationState.siem_api_key,
                    IntegrationState.save_siem_config,
                    IntegrationState.test_siem_connection,
                    IntegrationState.is_saving_siem,
                    IntegrationState.siem_connection_status,
                ),
                integration_config_card(
                    "RMM",
                    rmm_providers,
                    IntegrationState.rmm_provider,
                    IntegrationState.rmm_endpoint,
                    IntegrationState.rmm_api_key,
                    IntegrationState.save_rmm_config,
                    IntegrationState.test_rmm_connection,
                    IntegrationState.is_saving_rmm,
                    IntegrationState.rmm_connection_status,
                ),
                runtime_evidence_table(),
                class_name="grid grid-cols-1 lg:grid-cols-2 gap-8",
            ),
            locked_feature(
                feature_name="SIEM/RMM Integration", required_tier="enterprise"
            ),
        ),
        class_name="p-8",
    )