import reflex as rx
from app.components.sidebar import sidebar
from app.components.header import header
from app.pages.dashboard import dashboard_page
from app.pages.analytics import analytics_page as analytics_page_component
from app.pages.settings import settings_page
from app.pages.profile import profile_page
from app.pages.tech_stack import tech_stack_page
from app.pages.reporting import reporting_page
from app.pages.analysis import analysis_page
from app.pages.login import login_page
from app.pages.register import register_page
from app.pages.forgot_password import forgot_password_page
from app.pages.reset_password import reset_password_page
from app.pages.onboarding import onboarding_page
from app.pages.api_health import api_health_page
from app.pages.billing import billing_page
from app.pages.gap_analysis import gap_analysis_page
from app.pages.backlog_dashboard import backlog_dashboard_page
from app.pages.data_integrity import data_integrity_page
from app.components.admin_sidebar import admin_sidebar
from app.components.upgrade_prompts import upgrade_modal
from app.pages.tools.index import tools_index_page
from app.pages.tools.ssvc_calculator import ssvc_calculator_page
from app.pages.risk_intelligence import risk_intelligence_page
from app.pages.framework_config import framework_config_page
from app.pages.ai_config import ai_config_page


def create_page(content: rx.Component) -> rx.Component:
    """A template for creating pages with the sidebar layout."""
    return rx.el.div(
        sidebar(),
        rx.el.div(
            header(),
            rx.el.main(
                content, class_name="flex-1 font-['Montserrat'] bg-gray-50 min-h-screen"
            ),
            upgrade_modal(),
            class_name="flex flex-col ml-[250px] w-[calc(100%-250px)]",
        ),
        class_name="flex",
    )


def create_admin_page(content: rx.Component) -> rx.Component:
    """A template for creating admin pages with the admin sidebar layout."""
    return rx.el.div(
        admin_sidebar(),
        rx.el.div(
            header(),
            rx.el.main(
                content, class_name="flex-1 font-['Montserrat'] bg-gray-50 min-h-screen"
            ),
            class_name="flex flex-col ml-[250px] w-[calc(100%-250px)]",
        ),
        class_name="flex",
    )


def index() -> rx.Component:
    """The main index page, which defaults to the dashboard."""
    return create_page(dashboard_page())


def analytics_page_route() -> rx.Component:
    """The analytics page."""
    return create_page(analytics_page_component())


def settings() -> rx.Component:
    """The settings page."""
    return create_page(settings_page())


def profile() -> rx.Component:
    """The profile page."""
    return create_page(profile_page())


def tech_stack() -> rx.Component:
    """The tech stack page."""
    return create_page(tech_stack_page())


def reporting() -> rx.Component:
    """The reporting page."""
    return create_page(reporting_page())


def analysis() -> rx.Component:
    """The analysis page."""
    return create_page(analysis_page())


def billing() -> rx.Component:
    """The billing page."""
    return create_page(billing_page())


def gap_analysis() -> rx.Component:
    """The gap analysis page."""
    return create_page(gap_analysis_page())


def backlog_dashboard() -> rx.Component:
    """The CVE backlog dashboard page."""
    return create_page(backlog_dashboard_page())


def data_integrity() -> rx.Component:
    """The data integrity dashboard page."""
    return create_page(data_integrity_page())


def admin_api_health() -> rx.Component:
    """The admin API health page."""
    return create_admin_page(api_health_page())


def risk_intelligence() -> rx.Component:
    return create_page(risk_intelligence_page())


def framework_config() -> rx.Component:
    return create_page(framework_config_page())


def ai_config() -> rx.Component:
    return create_page(ai_config_page())


from app.pages.recommendations import recommendations_page


def recommendations() -> rx.Component:
    """The recommendations page."""
    return create_page(recommendations_page())


app = rx.App(
    theme=rx.theme(appearance="light"),
    head_components=[
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(rel="preconnect", href="https://fonts.gstatic.com", cross_origin=""),
        rx.el.link(
            href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;700&display=swap",
            rel="stylesheet",
        ),
    ],
)
app.add_page(index, route="/")
app.add_page(analytics_page_route, route="/analytics")
app.add_page(settings, route="/settings")
app.add_page(profile, route="/profile")
app.add_page(tech_stack, route="/tech_stack")
app.add_page(reporting, route="/reporting")
app.add_page(analysis, route="/analysis")
app.add_page(login_page, route="/login")
app.add_page(register_page, route="/register")
app.add_page(forgot_password_page, route="/forgot-password")
app.add_page(reset_password_page, route="/reset-password")
app.add_page(onboarding_page, route="/onboarding")
app.add_page(billing, route="/billing")
app.add_page(gap_analysis, route="/gap-analysis")
app.add_page(backlog_dashboard, route="/backlog-dashboard")
app.add_page(data_integrity, route="/data-integrity")
app.add_page(admin_api_health, route="/admin/api-health")
app.add_page(risk_intelligence, route="/risk-intelligence")
app.add_page(framework_config, route="/framework-config")
app.add_page(ai_config, route="/ai-config")
app.add_page(recommendations, route="/recommendations")
from app.pages.api_config import api_config_page

app.add_page(api_config_page, route="/api-config")
from app.pages.pricing import pricing_page

app.add_page(pricing_page, route="/pricing")
from app.pages.white_label_config import white_label_config_page

app.add_page(white_label_config_page, route="/white-label-config")
from app.pages.validation import validation_page

app.add_page(validation_page, route="/validation")
from app.pages.validation import validation_page

app.add_page(validation_page, route="/validation")
from app.pages.validation import validation_page

app.add_page(validation_page, route="/validation")
app.add_page(tools_index_page, route="/tools")
app.add_page(ssvc_calculator_page, route="/tools/ssvc-calculator")
from app.pages.inference_demo import inference_demo_page
from app.pages.runtime_correlation import runtime_correlation_page
from app.pages.exploit_intelligence import exploit_intelligence_page

app.add_page(inference_demo_page, route="/inference-demo")
app.add_page(runtime_correlation_page, route="/integrations/runtime-correlation")
app.add_page(exploit_intelligence_page, route="/exploit-intelligence")
from app.utils.scheduler import initialize_scheduler, shutdown_scheduler
from app.states.framework_state import FrameworkState
from app.utils.recommendation_migration import get_recommendation_migration_script
from app.utils.alerting_migration import get_alerting_migration_script
from app.utils.white_label_migration import get_white_label_migration_script
from app.utils.api_migration import get_api_migration_script
from app.utils.inference_migration import get_inference_migration_script
from app.utils.feedback_migration import get_feedback_migration_script
from app.utils.runtime_correlation_migration import (
    get_runtime_correlation_migration_script,
)
from app.utils.exploit_intelligence_migration import (
    get_exploit_intelligence_migration_script,
)
from app.utils.validation_migration import get_validation_migration_script


async def on_app_startup():
    """Initializes schedulers and fetches the KEV catalog."""
    initialize_scheduler()
    temp_state = FrameworkState()
    await temp_state.fetch_kev_catalog()


app.on_startup = on_app_startup
app.on_shutdown = shutdown_scheduler