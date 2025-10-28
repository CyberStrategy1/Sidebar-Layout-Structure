import reflex as rx
from typing import TypedDict, Literal
import random
import asyncio
from datetime import datetime, timedelta


class ValidationRecord(TypedDict):
    id: int
    cve_id: str
    framework: str
    predicted_score: float
    ground_truth_score: float
    is_correct: bool
    error_margin: float
    validated_at: str


class FrameworkPerformance(TypedDict):
    framework: str
    precision: float
    recall: float
    f1_score: float
    accuracy: float


class AutoTuneEvent(TypedDict):
    id: int
    timestamp: str
    framework: str
    old_weight: float
    new_weight: float
    reason: str


class ValidationState(rx.State):
    """State for evidence-based validation, accuracy tracking, and automated tuning."""

    is_loading: bool = True
    auto_tuning_enabled: bool = True
    validation_history: list[ValidationRecord] = []
    performance_metrics: list[FrameworkPerformance] = []
    tuning_history: list[AutoTuneEvent] = []
    last_run_time: str = "Never"

    @rx.event(background=True)
    async def load_validation_data(self):
        """Simulate loading validation data and calculating metrics."""
        async with self:
            self.is_loading = True
        await asyncio.sleep(2)
        history = []
        for i in range(100):
            predicted = round(random.uniform(20, 100), 1)
            actual = predicted + round(random.uniform(-15, 15), 1)
            actual = max(0, min(100, actual))
            history.append(
                {
                    "id": i,
                    "cve_id": f"CVE-2024-3{i:04}",
                    "framework": random.choice(["CVSS", "EPSS", "SSVC", "VPR", "PXS"]),
                    "predicted_score": predicted,
                    "ground_truth_score": actual,
                    "is_correct": abs(predicted - actual) < 5,
                    "error_margin": round(abs(predicted - actual), 1),
                    "validated_at": (
                        datetime.now() - timedelta(minutes=i * 10)
                    ).isoformat(),
                }
            )
        performance = []
        frameworks = ["CVSS", "EPSS", "SSVC", "VPR", "PXS"]
        for f in frameworks:
            accuracy = round(random.uniform(0.75, 0.98), 2)
            if f == "VPR":
                accuracy = 0.82
            performance.append(
                {
                    "framework": f,
                    "precision": round(random.uniform(0.8, 0.99), 2),
                    "recall": round(random.uniform(0.8, 0.99), 2),
                    "f1_score": round(random.uniform(0.8, 0.99), 2),
                    "accuracy": accuracy,
                }
            )
        tuning_events = [
            {
                "id": 1,
                "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
                "framework": "EPSS",
                "old_weight": 0.3,
                "new_weight": 0.35,
                "reason": "Accuracy dropped to 84%. Re-calibrating to boost signal.",
            }
        ]
        async with self:
            self.validation_history = history
            self.performance_metrics = performance
            self.tuning_history = tuning_events
            self.last_run_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
            self.is_loading = False
        yield ValidationState.check_and_run_auto_tune
        yield ValidationState.check_for_accuracy_alerts

    @rx.event(background=True)
    async def check_for_accuracy_alerts(self):
        """Checks for significant drops in accuracy and triggers an alert."""
        from app.states.alerting_state import AlertingState

        async with self:
            alerting_state = await self.get_state(AlertingState)
            for metric in self.performance_metrics:
                if metric["accuracy"] < 0.85:
                    await alerting_state.trigger_alert(
                        severity="CRITICAL",
                        title=f"Accuracy Drop Detected for {metric['framework']}",
                        description=f"The validation accuracy for the {metric['framework']} framework has dropped to {metric['accuracy'] * 100:.1f}%. Manual review and potential re-tuning are recommended.",
                        source="Validation Hub",
                    )

    @rx.event(background=True)
    async def check_and_run_auto_tune(self):
        """Check framework performance and trigger auto-tuning if needed."""
        if not self.auto_tuning_enabled:
            yield rx.toast.info("Auto-tuning is disabled.")
            return
        for metric in self.performance_metrics:
            if metric["accuracy"] < 0.85:
                async with self:
                    new_event = {
                        "id": len(self.tuning_history) + 1,
                        "timestamp": datetime.now().isoformat(),
                        "framework": metric["framework"],
                        "old_weight": round(random.uniform(0.1, 0.3), 2),
                        "new_weight": round(random.uniform(0.3, 0.5), 2),
                        "reason": f"Accuracy dropped to {int(metric['accuracy'] * 100)}%. Boosting weight to improve performance.",
                    }
                    self.tuning_history.append(new_event)
                yield rx.toast.warning(
                    f"Auto-tuning triggered for {metric['framework']} due to low accuracy."
                )

    @rx.event
    def toggle_auto_tuning(self, enabled: bool):
        """Enable or disable the auto-tuning feature."""
        self.auto_tuning_enabled = enabled
        if enabled:
            yield rx.toast.success("Automated tuning has been enabled.")
        else:
            yield rx.toast.info("Automated tuning has been disabled.")

    @rx.var
    def overall_accuracy(self) -> float:
        if not self.performance_metrics:
            return 0.0
        total_accuracy = sum((m["accuracy"] for m in self.performance_metrics))
        return round(total_accuracy / len(self.performance_metrics) * 100, 1)

    @rx.var
    def accuracy_trend(self) -> list[dict]:
        trend_data = []
        for i in range(30):
            date = (datetime.now() - timedelta(days=29 - i)).strftime("%b %d")
            accuracy = 90 + i / 30 * 5 - random.uniform(-2, 2)
            trend_data.append({"date": date, "accuracy": round(accuracy, 1)})
        return trend_data

    @rx.var
    def error_logs(self) -> list[ValidationRecord]:
        """Filter for records that are incorrect."""
        return [rec for rec in self.validation_history if not rec["is_correct"]]