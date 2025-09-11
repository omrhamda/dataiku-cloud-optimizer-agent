"""Lightweight notifiers for DSS plugin."""
from __future__ import annotations
from typing import Any, Dict, Optional
import json
import urllib.request

class SlackNotifier:
    def __init__(self, webhook_url: str | None) -> None:
        self.webhook_url = webhook_url

    def send(self, message: str, **kwargs: Any) -> bool:
        if not self.webhook_url:
            return False
        payload = {"text": message}
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(self.webhook_url, data=data, headers={"Content-Type": "application/json"})
        try:  # pragma: no cover - network
            with urllib.request.urlopen(req, timeout=5) as resp:  # nosec B310
                return 200 <= resp.getcode() < 300
        except Exception:
            return False

class EmailNotifier:
    def __init__(self, recipients: str | None) -> None:
        # For demonstration; real implementation would integrate with DSS mail
        self.recipients = [r.strip() for r in recipients.split(',')] if recipients else []

    def send(self, message: str, **kwargs: Any) -> bool:
        # Placeholder: In DSS you might push to a managed folder or use scenario reporter
        return bool(self.recipients)
