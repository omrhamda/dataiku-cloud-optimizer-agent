"""
Notification utilities for sending proactive updates to users.
"""

import os
import smtplib
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, Any

from slack_sdk import WebClient


class Notifier:
    """Basic interface for notifiers."""

    def send(self, message: str, **kwargs: Any) -> None:  # pragma: no cover - interface
        raise NotImplementedError


@dataclass
class SlackNotifier(Notifier):
    token: Optional[str] = None
    channel: Optional[str] = None

    def __post_init__(self) -> None:
        if self.token is None:
            self.token = os.getenv("SLACK_BOT_TOKEN")
        self._client = WebClient(token=self.token) if self.token else None

    def send(self, message: str, **kwargs: Any) -> None:
        if not self._client or not self.channel:
            raise RuntimeError("Slack client not configured or missing channel")
        self._client.chat_postMessage(channel=self.channel, text=message)


@dataclass
class EmailNotifier(Notifier):
    smtp_host: str = ""
    smtp_port: int = 587
    username: str = ""
    password: str = ""
    from_addr: str = ""
    to_addr: str = ""
    use_tls: bool = True

    def send(
        self, message: str, subject: str = "Cloud Optimization Update", **kwargs: Any
    ) -> None:
        if not all(
            [self.smtp_host, self.username, self.password, self.from_addr, self.to_addr]
        ):
            raise RuntimeError("Email notifier is not fully configured")

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.from_addr
        msg["To"] = self.to_addr
        part1 = MIMEText(message, "plain")
        msg.attach(part1)

        server = smtplib.SMTP(self.smtp_host, self.smtp_port)
        try:
            if self.use_tls:
                server.starttls()
            server.login(self.username, self.password)
            server.sendmail(self.from_addr, [self.to_addr], msg.as_string())
        finally:
            server.quit()
