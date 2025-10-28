import reflex as rx
from app.states.auth_state import AuthState


def register_page() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.h2(
                    "Create your account",
                    class_name="text-center text-3xl font-bold tracking-tight text-gray-900",
                ),
                class_name="mx-auto w-full max-w-sm lg:w-96",
            ),
            rx.el.div(
                rx.el.form(
                    rx.el.div(
                        rx.el.label(
                            "Email address",
                            class_name="block text-sm font-medium leading-6 text-gray-900",
                        ),
                        rx.el.div(
                            rx.el.input(
                                type="email",
                                name="email",
                                required=True,
                                class_name="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-teal-600 sm:text-sm sm:leading-6",
                            ),
                            class_name="mt-2",
                        ),
                    ),
                    rx.el.div(
                        rx.el.label(
                            "Password",
                            class_name="block text-sm font-medium leading-6 text-gray-900",
                        ),
                        rx.el.div(
                            rx.el.input(
                                type="password",
                                name="password",
                                required=True,
                                class_name="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-teal-600 sm:text-sm sm:leading-6",
                            ),
                            class_name="mt-2",
                        ),
                    ),
                    rx.el.div(
                        rx.el.label(
                            "Confirm Password",
                            class_name="block text-sm font-medium leading-6 text-gray-900",
                        ),
                        rx.el.div(
                            rx.el.input(
                                type="password",
                                name="confirm_password",
                                required=True,
                                class_name="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-teal-600 sm:text-sm sm:leading-6",
                            ),
                            class_name="mt-2",
                        ),
                        rx.cond(
                            AuthState.password_strength_error != "",
                            rx.el.p(
                                AuthState.password_strength_error,
                                class_name="text-xs text-red-500 mt-1",
                            ),
                            None,
                        ),
                        rx.cond(
                            AuthState.password_mismatch,
                            rx.el.p(
                                "Passwords do not match.",
                                class_name="text-xs text-red-500 mt-1",
                            ),
                            None,
                        ),
                    ),
                    rx.el.div(
                        rx.el.button(
                            "Create account",
                            type="submit",
                            is_loading=AuthState.is_loading,
                            class_name="flex w-full justify-center rounded-md bg-teal-400 px-3 py-1.5 text-sm font-semibold leading-6 text-white shadow-sm hover:bg-teal-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-600",
                        )
                    ),
                    rx.cond(
                        AuthState.error_message != "",
                        rx.el.div(
                            AuthState.error_message,
                            class_name="mt-4 text-center text-sm text-red-600",
                        ),
                        None,
                    ),
                    on_submit=AuthState.sign_up,
                    class_name="space-y-6",
                ),
                rx.el.p(
                    "Already have an account? ",
                    rx.el.a(
                        "Sign in",
                        href="/login",
                        class_name="font-semibold leading-6 text-teal-600 hover:text-teal-500",
                    ),
                    class_name="mt-10 text-center text-sm text-gray-500",
                ),
                class_name="mt-10",
            ),
            class_name="flex min-h-full flex-col justify-center px-6 py-12 lg:px-8",
        ),
        class_name="h-screen bg-gray-50 font-['Montserrat']",
    )