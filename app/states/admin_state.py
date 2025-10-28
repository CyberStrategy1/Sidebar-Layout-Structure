import reflex as rx
import os
from groq import Groq
import logging
from app.utils import supabase_client


class AdminState(rx.State):
    """State for the admin console, including API health monitoring."""

    api_health_logs: list[dict[str, str | int | float | bool | None]] = []
    is_loading: bool = False
    selected_log_id: str = ""
    diagnostic_result: dict[str, str] = {}
    is_diagnosing: bool = False

    @rx.event(background=True)
    async def fetch_api_health_logs(self):
        """Fetches API health logs from the Supabase table."""
        async with self:
            self.is_loading = True
            self.api_health_logs = []
        try:
            logs = await supabase_client.get_api_health_logs()
            async with self:
                self.api_health_logs = logs
        except Exception as e:
            logging.exception(f"Failed to fetch API health logs: {e}")
        finally:
            async with self:
                self.is_loading = False

    @rx.event(background=True)
    async def diagnose_with_ai(self, log_id: str, api_name: str, error_message: str):
        """Uses Groq to diagnose a failed API call."""
        str_log_id = str(log_id)
        async with self:
            self.is_diagnosing = True
            self.selected_log_id = str_log_id
        try:
            groq_api_key = os.getenv("GROQ_API_KEY")
            if not groq_api_key:
                advice = "Error: GROQ_API_KEY is not configured. Please set the environment variable to enable AI diagnostics."
            else:
                client = Groq(api_key=groq_api_key)
                response = client.chat.completions.create(
                    model="llama-3.1-70b-versatile",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert API troubleshooting assistant. Provide concise, actionable advice for fixing API errors.",
                        },
                        {
                            "role": "user",
                            "content": f"API Name: {api_name}\\nError: {error_message}\\n\\nProvide troubleshooting steps to fix this error.",
                        },
                    ],
                    temperature=0.7,
                    max_tokens=1024,
                )
                advice = response.choices[0].message.content
            async with self:
                self.diagnostic_result[log_id] = advice
        except Exception as e:
            logging.exception(f"AI diagnosis failed for log {log_id}: {e}")
            async with self:
                self.diagnostic_result[log_id] = (
                    f"An error occurred during diagnosis: {str(e)}"
                )
        finally:
            async with self:
                self.is_diagnosing = False
                self.selected_log_id = ""