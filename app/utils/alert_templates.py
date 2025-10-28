from typing import TypedDict


class Alert(TypedDict):
    id: int
    timestamp: str
    severity: str
    title: str
    description: str
    source: str


class Recipient(TypedDict):
    name: str


SEVERITY_COLORS = {
    "INFO": "#36a2eb",
    "WARNING": "#ffcc56",
    "CRITICAL": "#ff6384",
    "EMERGENCY": "#c90000",
}


def format_slack_message(alert: Alert, recipient: Recipient) -> dict:
    """Creates a rich Slack message using Block Kit."""
    color = SEVERITY_COLORS.get(alert["severity"], "#cccccc")
    return {
        "attachments": [
            {
                "color": color,
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*<{alert['source']}|{alert['title']}>*",
                        },
                    },
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": alert["description"]},
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Severity:* {alert['severity']}",
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Timestamp:* {alert['timestamp']}",
                            },
                        ],
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "Acknowledge"},
                                "style": "primary",
                                "value": f"ack_{alert['id']}",
                            },
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "Resolve"},
                                "value": f"resolve_{alert['id']}",
                            },
                        ],
                    },
                ],
            }
        ]
    }


def format_email_html(alert: Alert, recipient: Recipient) -> str:
    """Creates an HTML email template for an alert."""
    color = SEVERITY_COLORS.get(alert["severity"], "#cccccc")
    return f"""\n    <!DOCTYPE html>\n    <html>\n    <head>\n        <style>\n            body {{ font-family: Arial, sans-serif; margin: 20px; color: #333; }}\n            .container {{ border-left: 5px solid {color}; padding: 15px; background-color: #f9f9f9; border-radius: 5px; }}\n            h1 {{ color: {color}; margin-top: 0; }}\n            p {{ line-height: 1.6; }}\n            .footer {{ font-size: 12px; color: #888; margin-top: 20px; }}\n        </style>\n    </head>\n    <body>\n        <div class="container">\n            <h1>{alert["severity"]}: {alert["title"]}</h1>\n            <p>Hi {recipient["name"]},</p>\n            <p>{alert["description"]}</p>\n            <p><strong>Source:</strong> {alert["source"]}<br>\n               <strong>Timestamp:</strong> {alert["timestamp"]}</p>\n        </div>\n        <div class="footer">This is an automated alert from Aperture Enterprise.</div>\n    </body>\n    </html>\n    """