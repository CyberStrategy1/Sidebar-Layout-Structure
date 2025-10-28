import reflex as rx
from app.states.onboarding_state import OnboardingState
from app.states.auth_state import AuthState


def progress_indicator() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(class_name="absolute w-1/2 h-0.5 bg-teal-600 top-1/2 left-0"),
            rx.el.div(
                class_name=rx.cond(
                    OnboardingState.current_step > 1,
                    "absolute w-1/2 h-0.5 bg-teal-600 top-1/2 right-0",
                    "absolute w-1/2 h-0.5 bg-gray-200 top-1/2 right-0",
                )
            ),
            rx.el.div(
                rx.el.div(
                    "1",
                    class_name="flex items-center justify-center w-6 h-6 rounded-full bg-teal-600 text-xs font-semibold text-white",
                ),
                class_name="relative z-10 flex items-center justify-center w-8 h-8 bg-white border-2 border-teal-600 rounded-full",
            ),
            rx.el.div(
                rx.el.div(
                    "2",
                    class_name=rx.cond(
                        OnboardingState.current_step >= 2,
                        "flex items-center justify-center w-6 h-6 rounded-full bg-teal-600 text-xs font-semibold text-white",
                        "flex items-center justify-center w-6 h-6 rounded-full bg-gray-200 text-xs font-semibold text-gray-500",
                    ),
                ),
                class_name=rx.cond(
                    OnboardingState.current_step >= 2,
                    "relative z-10 flex items-center justify-center w-8 h-8 bg-white border-2 border-teal-600 rounded-full",
                    "relative z-10 flex items-center justify-center w-8 h-8 bg-white border-2 border-gray-200 rounded-full",
                ),
            ),
            rx.el.div(
                rx.el.div(
                    "3",
                    class_name=rx.cond(
                        OnboardingState.current_step == 3,
                        "flex items-center justify-center w-6 h-6 rounded-full bg-teal-600 text-xs font-semibold text-white",
                        "flex items-center justify-center w-6 h-6 rounded-full bg-gray-200 text-xs font-semibold text-gray-500",
                    ),
                ),
                class_name=rx.cond(
                    OnboardingState.current_step == 3,
                    "relative z-10 flex items-center justify-center w-8 h-8 bg-white border-2 border-teal-600 rounded-full",
                    "relative z-10 flex items-center justify-center w-8 h-8 bg-white border-2 border-gray-200 rounded-full",
                ),
            ),
            class_name="relative flex items-center justify-between w-full",
        ),
        class_name="w-full max-w-xs mx-auto mb-8",
    )


def onboarding_step_1() -> rx.Component:
    return rx.el.div(
        rx.el.h3(
            "Step 1 of 3: Your Information",
            class_name="font-semibold text-gray-500 mb-4",
        ),
        rx.el.form(
            rx.el.div(
                rx.el.label(
                    "Full Name",
                    class_name="block text-sm font-medium text-gray-700 mb-1",
                ),
                rx.el.input(
                    name="full_name",
                    placeholder="John Doe",
                    required=True,
                    class_name="w-full p-2 border border-gray-300 rounded-md shadow-sm",
                ),
                class_name="mb-4",
            ),
            rx.el.div(
                rx.el.label(
                    "Job Title",
                    class_name="block text-sm font-medium text-gray-700 mb-1",
                ),
                rx.el.input(
                    name="job_title",
                    placeholder="Security Analyst",
                    required=True,
                    class_name="w-full p-2 border border-gray-300 rounded-md shadow-sm",
                ),
                class_name="mb-4",
            ),
            rx.el.div(
                rx.el.label(
                    "Organization Name",
                    class_name="block text-sm font-medium text-gray-700 mb-1",
                ),
                rx.el.input(
                    name="org_name",
                    placeholder="Acme Inc.",
                    required=True,
                    class_name="w-full p-2 border border-gray-300 rounded-md shadow-sm",
                ),
                class_name="mb-6",
            ),
            rx.el.button(
                "Create Organization & Continue",
                type="submit",
                class_name="w-full bg-teal-400 text-white py-2 rounded-md font-semibold hover:bg-teal-500 transition disabled:opacity-50",
                is_loading=OnboardingState.is_loading,
            ),
            on_submit=OnboardingState.handle_step_1,
            reset_on_submit=True,
        ),
    )


def onboarding_step_2() -> rx.Component:
    return rx.el.div(
        rx.el.h3(
            "Step 2 of 3: Asset & Context",
            class_name="font-semibold text-gray-500 mb-4",
        ),
        rx.el.form(
            rx.el.div(
                rx.el.label("Primary Cloud Provider", class_name="text-sm font-medium"),
                rx.el.select(
                    rx.el.option("Select a provider...", value="", disabled=True),
                    rx.el.option("AWS", value="aws"),
                    rx.el.option("GCP", value="gcp"),
                    rx.el.option("Azure", value="azure"),
                    rx.el.option("Multi-Cloud", value="multi-cloud"),
                    rx.el.option("On-Premise", value="on-prem"),
                    name="cloud_provider",
                    class_name="w-full mt-1 p-2 border border-gray-300 rounded-md shadow-sm",
                    required=True,
                ),
                class_name="mb-4",
            ),
            rx.el.div(
                rx.el.label(
                    "Internet-Exposed IP Ranges (CIDR)",
                    class_name="text-sm font-medium",
                ),
                rx.el.textarea(
                    name="ip_ranges",
                    placeholder="e.g., 192.168.1.0/24, 10.0.0.0/8",
                    class_name="w-full mt-1 p-2 border border-gray-300 rounded-md shadow-sm font-mono",
                ),
                class_name="mb-4",
            ),
            rx.el.div(
                rx.el.label("Upload SBOM", class_name="text-sm font-medium"),
                rx.upload.root(
                    rx.el.div(
                        rx.icon("file-up", class_name="w-8 h-8 text-gray-400"),
                        rx.el.p(
                            "Drag & drop or click to upload SBOM file (JSON, XML)",
                            class_name="text-xs text-gray-500",
                        ),
                        class_name="flex flex-col items-center justify-center p-4 border-2 border-dashed rounded-lg",
                    ),
                    id="sbom_upload",
                    accept={
                        "application/json": [".json"],
                        "application/xml": [".xml"],
                        "text/xml": [".xml"],
                    },
                    max_files=1,
                    class_name="w-full mt-1",
                ),
                rx.foreach(
                    rx.selected_files("sbom_upload"),
                    lambda file: rx.el.div(
                        file, class_name="text-sm text-gray-600 mt-2"
                    ),
                ),
                rx.el.button(
                    "Process SBOM",
                    on_click=OnboardingState.handle_sbom_upload(
                        rx.upload_files(upload_id="sbom_upload")
                    ),
                    is_loading=OnboardingState.is_uploading,
                    class_name="text-sm mt-2 bg-gray-200 px-3 py-1 rounded-md font-semibold",
                ),
                class_name="mb-4",
            ),
            rx.el.button(
                "Save Context & Continue",
                type="submit",
                class_name="w-full bg-teal-400 text-white py-2 rounded-md font-semibold hover:bg-teal-500 transition",
                is_loading=OnboardingState.is_loading,
            ),
            on_submit=OnboardingState.handle_step_2,
            reset_on_submit=True,
        ),
    )


def onboarding_step_3() -> rx.Component:
    return rx.el.div(
        rx.el.h3(
            "Step 3 of 3: Your Tech Stack",
            class_name="font-semibold text-gray-500 mb-4",
        ),
        rx.el.p(
            "Add at least 3 technologies your organization uses. We've pre-filled some from your SBOM.",
            class_name="text-sm text-gray-600 mb-4",
        ),
        rx.el.div(
            rx.el.input(
                placeholder="e.g., PostgreSQL, React, AWS",
                on_change=OnboardingState.set_new_tech_item,
                default_value=OnboardingState.new_tech_item,
                class_name="flex-grow p-2 border border-gray-300 rounded-l-md",
            ),
            rx.el.button(
                "Add",
                on_click=OnboardingState.add_tech_item,
                class_name="bg-gray-200 text-gray-700 px-4 py-2 rounded-r-md font-semibold hover:bg-gray-300 transition",
            ),
            class_name="flex mb-4",
        ),
        rx.el.div(
            rx.foreach(
                OnboardingState.tech_stack,
                lambda item: rx.el.span(
                    item,
                    class_name="bg-gray-100 text-gray-800 px-3 py-1 rounded-full text-sm font-medium",
                ),
            ),
            class_name="flex flex-wrap gap-2 mb-6 min-h-[40px]",
        ),
        rx.el.button(
            "Complete Onboarding",
            on_click=OnboardingState.complete_onboarding,
            disabled=OnboardingState.tech_stack.length() < 3,
            class_name="w-full bg-teal-400 text-white py-2 rounded-md font-semibold hover:bg-teal-500 transition disabled:opacity-50 disabled:cursor-not-allowed",
            is_loading=OnboardingState.is_loading,
        ),
    )


def onboarding_page() -> rx.Component:
    """The user onboarding page with a multi-step modal."""
    return rx.el.div(
        rx.el.div(
            rx.el.h1(
                "Welcome to Aperture!",
                class_name="text-3xl font-bold text-gray-800 mb-2",
            ),
            rx.el.p(
                f"Let's get your account set up, {AuthState.email}.",
                class_name="text-gray-600 mb-8",
            ),
            progress_indicator(),
            rx.match(
                OnboardingState.current_step,
                (1, onboarding_step_1()),
                (2, onboarding_step_2()),
                (3, onboarding_step_3()),
                rx.el.div("Loading..."),
            ),
            rx.cond(
                OnboardingState.error_message != "",
                rx.el.div(
                    rx.el.p(
                        OnboardingState.error_message,
                        class_name="text-red-500 text-sm mt-4 text-center",
                    ),
                    class_name="bg-red-50 border border-red-200 p-3 rounded-md mt-4",
                ),
                None,
            ),
            class_name="w-full max-w-lg bg-white p-8 rounded-xl shadow-lg border border-gray-200",
        ),
        class_name="flex items-center justify-center min-h-screen bg-gray-50 p-4 font-['Montserrat']",
        on_mount=OnboardingState.on_load,
    )