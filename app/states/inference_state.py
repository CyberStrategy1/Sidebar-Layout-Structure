import reflex as rx
from typing import Optional
import json


class InferenceState(rx.State):
    """State for managing the AI inference engine demonstration."""

    is_inferring: bool = False
    cve_id_input: str = "CVE-2024-21412"
    inference_result: Optional[dict] = None
    error_message: str = ""

    @rx.var
    def formatted_result(self) -> str:
        """Return the inference result as a formatted JSON string."""
        if self.inference_result:
            return json.dumps(self.inference_result, indent=2)
        return ""

    @rx.event(background=True)
    async def run_inference(self):
        """Trigger the inference pipeline for the given CVE ID."""
        async with self:
            if not self.cve_id_input:
                self.error_message = "CVE ID cannot be empty."
                yield rx.toast.error(self.error_message)
                return
            self.is_inferring = True
            self.error_message = ""
            self.inference_result = None
        try:
            import asyncio
            import random

            await asyncio.sleep(2.5)
            mock_result = {
                "cve_id": self.cve_id_input,
                "predicted_severity": "HIGH",
                "severity_confidence": 0.8921,
                "predicted_epss": 0.7532,
                "exploitation_likelihood": "High",
                "processing_time_ms": 2451,
                "model_version": "0.1.0",
            }
            async with self:
                self.inference_result = mock_result
                yield rx.toast.success(f"Inference complete for {self.cve_id_input}")
        except Exception as e:
            logging.exception(f"Inference failed: {e}")
            async with self:
                self.error_message = f"An error occurred: {e}"
                yield rx.toast.error(self.error_message)
        finally:
            async with self:
                self.is_inferring = False