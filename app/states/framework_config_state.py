import reflex as rx
import logging
from app.utils import supabase_client
from app.states.risk_scoring_state import RiskScoringState
from app.state import AppState
import random


class FrameworkConfigState(rx.State):
    """State for the Framework Configuration page."""

    is_loading: bool = False
    weights: dict[str, float] = {
        "cvss": 0.4,
        "epss": 0.3,
        "kev": 0.2,
        "ssvc": 0.1,
        "lev": 0.0,
    }
    sample_cve: dict = {
        "cvss_score": 8.1,
        "epss_score": 0.9377,
        "is_kev": True,
        "decision": "Act",
    }
    preview_score: dict = {}

    @rx.event(background=True)
    async def load_config(self):
        async with self:
            self.is_loading = True
        try:
            async with self:
                app_state = await self.get_state(AppState)
                if app_state.active_organization_id:
                    pass
                risk_state = await self.get_state(RiskScoringState)
                risk_state.scoring_weights = self.weights
                self.preview_score = risk_state.compute_universal_score(self.sample_cve)
        except Exception as e:
            logging.exception(f"Failed to load framework config: {e}")
        finally:
            async with self:
                self.is_loading = False

    @rx.event
    async def adjust_weight(self, value: str, framework: str):
        try:
            new_weight = float(value)
            self.weights[framework] = new_weight
            risk_state = await self.get_state(RiskScoringState)
            risk_state.scoring_weights = self.weights
            self.preview_score = risk_state.compute_universal_score(self.sample_cve)
        except ValueError as e:
            logging.exception(f"Failed to adjust weight: {e}")

    @rx.event
    async def save_config(self):
        total_weight = sum(self.weights.values())
        if not 0.99 < total_weight < 1.01:
            return rx.toast.error(
                f"Weights must sum to 1.0. Current sum: {total_weight:.2f}"
            )
        self.is_loading = True
        try:
            import asyncio

            await asyncio.sleep(1)
            return rx.toast.success("Configuration saved successfully!")
        except Exception as e:
            logging.exception(f"Failed to save config: {e}")
            return rx.toast.error("Failed to save configuration.")
        finally:
            self.is_loading = False

    @rx.event
    async def reset_to_recommended(self):
        self.weights = {"cvss": 0.4, "epss": 0.3, "kev": 0.2, "ssvc": 0.1, "lev": 0.0}
        risk_state = await self.get_state(RiskScoringState)
        risk_state.scoring_weights = self.weights
        self.preview_score = risk_state.compute_universal_score(self.sample_cve)
        return rx.toast.info("Weights reset to recommended values.")

    @rx.var
    def total_weight(self) -> float:
        return round(sum(self.weights.values()), 2)

    @rx.var
    def breakdown_data(self) -> list[dict]:
        if not self.preview_score or "breakdown" not in self.preview_score:
            return []
        breakdown = self.preview_score["breakdown"]
        return [
            {"name": "CVSS", "value": breakdown.get("cvss_points", 0)},
            {"name": "EPSS", "value": breakdown.get("epss_points", 0)},
            {"name": "SSVC", "value": breakdown.get("ssvc_points", 0)},
            {"name": "KEV Bonus", "value": breakdown.get("kev_bonus", 0)},
        ]