import reflex as rx
from typing import TypedDict, Any
from app.states.framework_state import FrameworkState


class RiskScoringState(rx.State):
    """Universal risk scoring engine that combines all frameworks."""

    scoring_weights: dict[str, float] = {
        "cvss": 0.4,
        "epss": 0.3,
        "kev": 0.2,
        "ssvc": 0.1,
        "lev": 0.0,
    }

    def _map_ssvc_to_numeric(self, ssvc_decision: str | None) -> int:
        """Map SSVC decision to a numeric value for scoring."""
        return {"Act": 100, "Attend": 70, "Track*": 50, "Track": 20}.get(
            ssvc_decision, 0
        )

    def _normalize_score(
        self, score: float, source_range: tuple, target_range: tuple
    ) -> float:
        """Normalize a score from a source range to a target range."""
        s_min, s_max = source_range
        t_min, t_max = target_range
        if s_max - s_min == 0:
            return t_min
        return t_min + (score - s_min) * (t_max - t_min) / (s_max - s_min)

    def _calculate_cohen_kappa(self, scores: list[dict]) -> float:
        """A mock calculation for inter-rater agreement among frameworks."""
        if len(scores) < 2:
            return 1.0
        numeric_scores = [
            s["normalized_score"]
            for s in scores
            if s.get("normalized_score") is not None
        ]
        if not numeric_scores or len(numeric_scores) < 2:
            return 0.0
        mean_score = sum(numeric_scores) / len(numeric_scores)
        variance = sum(((x - mean_score) ** 2 for x in numeric_scores)) / len(
            numeric_scores
        )
        agreement = 1 - variance / 2500
        return max(0.0, min(1.0, agreement))

    def _identify_conflicts(self, scores: dict, threshold: float = 30.0) -> list[str]:
        """Identify significant conflicts between framework scores."""
        conflicts = []
        cvss = scores.get("cvss_score", 0.0) or 0.0
        epss = scores.get("epss_score", 0.0) or 0.0
        if cvss >= 7.0 and epss < 0.02:
            conflicts.append("High CVSS, Low EPSS")
        if cvss < 5.0 and epss > 0.5:
            conflicts.append("Low CVSS, High EPSS")
        if scores.get("is_kev") and cvss < 7.0:
            conflicts.append("KEV with non-High CVSS")
        return conflicts

    def _calculate_confidence(self, scores: dict, agreement: float) -> float:
        """Calculate a confidence score based on data availability and agreement."""
        num_frameworks = len([s for s in scores if scores.get(s) is not None])
        base_confidence = self._normalize_score(num_frameworks, (1, 11), (0.5, 1.0))
        return min(1.0, base_confidence * (0.8 + agreement * 0.2))

    @rx.event
    def compute_universal_score(self, framework_data: dict) -> dict[str, Any]:
        """Calculate universal risk score (0-100) from all framework inputs."""
        cvss_score = framework_data.get("cvss_score", 0.0) or 0.0
        epss_score = framework_data.get("epss_score", 0.0) or 0.0
        is_kev = framework_data.get("is_kev", False)
        ssvc_decision = framework_data.get("decision")
        cvss_normalized = self._normalize_score(cvss_score, (0, 10), (0, 100))
        epss_normalized = epss_score * 100
        ssvc_numeric = self._map_ssvc_to_numeric(ssvc_decision)
        kev_bonus = 20 if is_kev else 0
        universal_score = (
            cvss_normalized * self.scoring_weights["cvss"]
            + epss_normalized * self.scoring_weights["epss"]
            + ssvc_numeric * self.scoring_weights["ssvc"]
        )
        final_score = min(100, universal_score + kev_bonus)
        normalized_scores_for_kappa = [
            {"name": "cvss", "normalized_score": cvss_normalized},
            {"name": "epss", "normalized_score": epss_normalized},
        ]
        agreement = self._calculate_cohen_kappa(normalized_scores_for_kappa)
        confidence = self._calculate_confidence(framework_data, agreement)
        conflicts = self._identify_conflicts(framework_data)
        return {
            "universal_risk_score": round(final_score, 2),
            "breakdown": {
                "cvss_points": round(cvss_normalized * self.scoring_weights["cvss"], 2),
                "epss_points": round(epss_normalized * self.scoring_weights["epss"], 2),
                "ssvc_points": round(ssvc_numeric * self.scoring_weights["ssvc"], 2),
                "kev_bonus": kev_bonus,
            },
            "framework_agreement": round(agreement, 2),
            "scoring_confidence": round(confidence, 2),
            "conflict_flags": conflicts,
        }

    @rx.event
    def adjust_weight(self, framework: str, new_weight: float):
        """Update scoring weight for a framework (for UI sliders)."""
        if framework in self.scoring_weights:
            self.scoring_weights[framework] = new_weight
            return rx.toast.info(
                f"Weight for {framework.upper()} updated to {new_weight:.2f}"
            )

    @rx.event
    def reset_to_recommended(self):
        """Reset weights to the platform-recommended defaults."""
        self.scoring_weights = {
            "cvss": 0.4,
            "epss": 0.3,
            "kev": 0.2,
            "ssvc": 0.1,
            "lev": 0.0,
        }
        return rx.toast.success(
            "Scoring weights have been reset to recommended values."
        )