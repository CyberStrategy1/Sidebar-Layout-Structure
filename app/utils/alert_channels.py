import reflex as rx
import logging
import httpx
import os
from typing import TypedDict, Literal
from app.utils.alert_templates import format_slack_message, format_email_html

AlertChannel = Literal["email", "slack", "sms", "pagerduty", "teams", "webhook"]


class Alert(TypedDict):
    id: int
    timestamp: str
    severity: str
    title: str
    description: str
    source: str


class Recipient(TypedDict):
    id: int
    name: str
    email: str
    phone: str
    slack_id: str


async def send_slack_alert(alert: Alert, recipient: Recipient) -> bool:
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        logging.warning("SLACK_WEBHOOK_URL not set. Skipping Slack alert.")
        return False
    payload = format_slack_message(alert, recipient)
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(webhook_url, json=payload)
            response.raise_for_status()
        logging.info(f"Slack alert sent for CVE {alert['title']}")
        return True
    except httpx.HTTPError as e:
        logging.exception(f"Failed to send Slack alert: {e}")
        return False


async def send_email_alert(alert: Alert, recipient: Recipient) -> bool:
    logging.info(
        f"Simulating email alert to {recipient['email']} for: {alert['title']}"
    )
    return True


async def send_sms_alert(alert: Alert, recipient: Recipient) -> bool:
    twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
    twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
    twilio_from = os.getenv("TWILIO_FROM_NUMBER")
    if not all([twilio_sid, twilio_token, twilio_from]):
        logging.warning("Twilio credentials not set. Simulating SMS alert.")
        logging.info(
            f"SMS to {recipient['phone']}: {alert['severity']} - {alert['title']}"
        )
        return True
    return True


async def send_pagerduty_alert(alert: Alert, recipient: Recipient) -> bool:
    api_key = os.getenv("PAGERDUTY_API_KEY")
    if not api_key:
        logging.warning("PAGERDUTY_API_KEY not set. Simulating PagerDuty alert.")
        logging.info(f"PagerDuty incident created for: {alert['title']}")
        return True
    return True


async def send_teams_alert(alert: Alert, recipient: Recipient) -> bool:
    webhook_url = os.getenv("TEAMS_WEBHOOK_URL")
    if not webhook_url:
        logging.warning("TEAMS_WEBHOOK_URL not set. Skipping Teams alert.")
        return False
    logging.info(f"Simulating Teams alert for: {alert['title']}")
    return True


async def send_webhook_alert(alert: Alert, recipient: Recipient) -> bool:
    webhook_url = os.getenv("CUSTOM_WEBHOOK_URL")
    if not webhook_url:
        return False
    try:
        async with httpx.AsyncClient() as client:
            await client.post(webhook_url, json=alert)
        return True
    except httpx.HTTPError as e:
        logging.exception(f"Failed to send webhook alert: {e}")
        return False


CHANNEL_MAP = {
    "slack": send_slack_alert,
    "email": send_email_alert,
    "sms": send_sms_alert,
    "pagerduty": send_pagerduty_alert,
    "teams": send_teams_alert,
    "webhook": send_webhook_alert,
}


async def send_alert_to_channel(
    channel: AlertChannel, alert: Alert, recipient: Recipient
):
    if handler := CHANNEL_MAP.get(channel):
        try:
            await handler(alert, recipient)
        except Exception as e:
            logging.exception(f"Error sending alert via {channel}: {e}")