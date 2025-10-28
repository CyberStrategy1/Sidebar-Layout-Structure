import reflex as rx
from typing import TypedDict, Literal, Optional
import random
from datetime import datetime, timedelta


class Recommendation(TypedDict):
    id: int
    recommendation_type: Literal[
        "adjust_weights", "enable_framework", "disable_framework", "change_provider"
    ]
    details: dict
    reasoning: str
    confidence_score: float
    impact_preview: dict
    status: Literal["pending", "applied", "dismissed", "ab_testing"]
    created_at: str


class RecommendationState(rx.State):
    """Manages the AI-powered recommendation engine."""

    recommendations: list[Recommendation] = []
    selected_recommendation: Optional[Recommendation] = None
    show_apply_modal: bool = False
    is_loading: bool = False
    is_generating: bool = False

    @rx.var
    def pending_recommendations(self) -> list[Recommendation]:
        """Returns recommendations with 'pending' status."""
        return [rec for rec in self.recommendations if rec["status"] == "pending"]

    @rx.event(background=True)
    async def generate_recommendations(self):
        """Generate mock recommendations for display."""
        import asyncio

        async with self:
            self.is_generating = True
            self.recommendations = []
        await asyncio.sleep(2)
        recs = [
            {
                "id": 1,
                "recommendation_type": "adjust_weights",
                "details": {"framework": "epss", "from": 0.3, "to": 0.45},
                "reasoning": "Your vulnerability profile shows a high number of exploited, low-CVSS vulnerabilities. Increasing EPSS weight will better prioritize real-world threats.",
                "confidence_score": 0.92,
                "impact_preview": {
                    "Affected CVEs": "~150",
                    "Avg. Score Change": "+5.2 pts",
                    "Priority Shifts": "+28 Critical",
                },
                "status": "pending",
                "created_at": (datetime.now() - timedelta(hours=2)).isoformat(),
            },
            {
                "id": 2,
                "recommendation_type": "change_provider",
                "details": {"from": "OpenAI GPT-4", "to": "Groq Llama-3.1"},
                "reasoning": "Groq offers comparable analysis quality for your use case at a significantly lower cost and higher speed.",
                "confidence_score": 0.98,
                "impact_preview": {
                    "Est. Cost Savings": "~70% ($250/mo)",
                    "Avg. Analysis Time": "-8 seconds",
                    "Quality Impact": "Negligible for current usage",
                },
                "status": "pending",
                "created_at": (datetime.now() - timedelta(days=1)).isoformat(),
            },
            {
                "id": 3,
                "recommendation_type": "adjust_weights",
                "details": {"framework": "kev", "from": 0.2, "to": 0.15},
                "reasoning": "Your tech stack has low exposure to KEV catalog vulnerabilities. Reducing its weight slightly allows for better distribution to more relevant factors like EPSS.",
                "confidence_score": 0.85,
                "impact_preview": {
                    "Affected CVEs": "~450",
                    "Avg. Score Change": "-1.8 pts",
                    "Priority Shifts": "-5 Critical",
                },
                "status": "dismissed",
                "created_at": (datetime.now() - timedelta(days=3)).isoformat(),
            },
        ]
        async with self:
            self.recommendations = recs
            self.is_generating = False

    @rx.event
    def select_recommendation_for_apply(self, rec_id: int):
        """Selects a recommendation and opens the apply modal."""
        for rec in self.recommendations:
            if rec["id"] == rec_id:
                self.selected_recommendation = rec
                self.show_apply_modal = True
                break

    @rx.event
    def close_apply_modal(self):
        """Closes the apply modal and clears selection."""
        self.show_apply_modal = False
        self.selected_recommendation = None

    @rx.event(background=True)
    async def apply_recommendation(self):
        """Applies the selected recommendation."""
        import asyncio

        rec_id = self.selected_recommendation["id"]
        rec_name = self.selected_recommendation["recommendation_type"]
        async with self:
            self.is_loading = True
        await asyncio.sleep(1)
        async with self:
            for i, rec in enumerate(self.recommendations):
                if rec["id"] == rec_id:
                    self.recommendations[i]["status"] = "applied"
                    break
            self.is_loading = False
            self.close_apply_modal()
            yield rx.toast.success(f"Recommendation '{rec_name}' applied successfully!")

    @rx.event
    def dismiss_recommendation(self, rec_id: int):
        """Dismisses a recommendation."""
        for i, rec in enumerate(self.recommendations):
            if rec["id"] == rec_id:
                self.recommendations[i]["status"] = "dismissed"
                yield rx.toast.info("Recommendation dismissed.")
                break

    @rx.event
    def start_ab_test(self):
        """Placeholder to start an A/B test."""
        self.close_apply_modal()
        return rx.toast.info("A/B test started. Results will be available in 24 hours.")