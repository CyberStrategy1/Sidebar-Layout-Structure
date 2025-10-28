import reflex as rx
from typing import TypedDict, Literal, Optional
import logging
from datetime import datetime, timedelta

AlertSeverity = Literal["INFO", "WARNING", "CRITICAL", "EMERGENCY"]
AlertChannel = Literal["email", "slack", "sms", "pagerduty", "teams", "webhook"]


class Alert(TypedDict):
    id: int
    timestamp: str
    severity: AlertSeverity
    title: str
    description: str
    source: str
    deduplication_key: str
    status: Literal["new", "acknowledged", "resolved"]


class EscalationPolicy(TypedDict):
    delay_minutes: int
    channels: list[AlertChannel]


class OnCallRecipient(TypedDict):
    id: int
    name: str
    email: str
    phone: str
    slack_id: str


class AlertingState(rx.State):
    """Manages alert routing, prioritization, and history."""

    alerts: list[Alert] = []
    alert_history: list[Alert] = []
    is_loading: bool = False
    last_alert_timestamps: dict[str, str] = {}
    deduplication_window_minutes: int = 5
    escalation_policies: dict[AlertSeverity, list[EscalationPolicy]] = {
        "INFO": [{"delay_minutes": 0, "channels": ["slack"]}],
        "WARNING": [{"delay_minutes": 0, "channels": ["slack", "email"]}],
        "CRITICAL": [
            {"delay_minutes": 0, "channels": ["slack", "sms"]},
            {"delay_minutes": 15, "channels": ["pagerduty"]},
        ],
        "EMERGENCY": [
            {"delay_minutes": 0, "channels": ["pagerduty", "sms"]},
            {"delay_minutes": 5, "channels": ["pagerduty"]},
        ],
    }
    on_call_schedule: list[OnCallRecipient] = [
        {
            "id": 1,
            "name": "Admin User",
            "email": "admin@example.com",
            "phone": "+15555555555",
            "slack_id": "U12345",
        }
    ]

    @rx.event(background=True)
    async def trigger_alert(
        self,
        severity: AlertSeverity,
        title: str,
        description: str,
        source: str,
        deduplication_key: Optional[str] = None,
    ):
        """Receives, deduplicates, and initiates the alert escalation process."""
        dedup_key = deduplication_key or f"{source}-{title}"
        last_alert_time_str = self.last_alert_timestamps.get(dedup_key)
        if last_alert_time_str:
            last_alert_time = datetime.fromisoformat(last_alert_time_str)
            if datetime.utcnow() - last_alert_time < timedelta(
                minutes=self.deduplication_window_minutes
            ):
                logging.info(f"Deduplicating alert with key: {dedup_key}")
                return
        async with self:
            self.last_alert_timestamps[dedup_key] = datetime.utcnow().isoformat()
            new_alert = {
                "id": len(self.alerts) + 1,
                "timestamp": datetime.utcnow().isoformat(),
                "severity": severity,
                "title": title,
                "description": description,
                "source": source,
                "deduplication_key": dedup_key,
                "status": "new",
            }
            self.alerts.append(new_alert)
            yield AlertingState.process_escalation(new_alert)

    @rx.event(background=True)
    async def process_escalation(self, alert: Alert):
        """Processes the escalation policies for a given alert."""
        import asyncio
        from app.utils.alert_channels import send_alert_to_channel

        policies = self.escalation_policies.get(alert["severity"], [])
        for policy in policies:
            await asyncio.sleep(policy["delay_minutes"] * 60)
            async with self:
                current_alert = next(
                    (a for a in self.alerts if a["id"] == alert["id"]), None
                )
                if not current_alert or current_alert["status"] != "new":
                    logging.info(
                        f"Alert {alert['id']} is no longer new. Halting escalation."
                    )
                    return
                for channel in policy["channels"]:
                    for recipient in self.on_call_schedule:
                        await send_alert_to_channel(channel, alert, recipient)

    @rx.event
    def acknowledge_alert(self, alert_id: int):
        """Mark an alert as acknowledged."""
        for i, alert in enumerate(self.alerts):
            if alert["id"] == alert_id:
                self.alerts[i]["status"] = "acknowledged"
                yield rx.toast.info(f"Alert '{alert['title']}' acknowledged.")
                break

    @rx.event
    def resolve_alert(self, alert_id: int):
        """Mark an alert as resolved and move to history."""
        alert_to_move = None
        for i, alert in enumerate(self.alerts):
            if alert["id"] == alert_id:
                alert_to_move = self.alerts.pop(i)
                break
        if alert_to_move:
            alert_to_move["status"] = "resolved"
            self.alert_history.insert(0, alert_to_move)
            yield rx.toast.success(f"Alert '{alert_to_move['title']}' resolved.")