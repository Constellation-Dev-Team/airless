import json
import smtplib

from typing import List

from airless.core.hook import EmailHook
from airless.core.utils import get_config

secret_locations = f'/secrets/{get_config("SECRET_SMTP")}'
with open(secret_locations) as f:
    SECRET = json.loads(f.read())


class GoogleEmailHook(EmailHook):
    """Hook for sending emails using Google Email service."""

    def __init__(self) -> None:
        """Initializes the GoogleEmailHook."""
        super().__init__()

    def send(
        self,
        subject: str,
        content: str,
        recipients: List[str],
        sender: str,
        attachments: List[dict],
        mime_type: str,
        timeout: int = 30,
    ) -> None:
        """Sends an email.

        Args:
            subject (str): The subject of the email.
            content (str): The content of the email.
            recipients (List[str]): The list of email recipients.
            sender (str): The sender's email address.
            attachments (List[dict]): The list of attachments.
            mime_type (str): The MIME type of the email content.
            timeout (int, optional): The SMTP connection timeout in seconds. Defaults to 30.
        """
        msg = self.build_message(
            subject, content, recipients, sender, attachments, mime_type
        )
        server = smtplib.SMTP_SSL(SECRET['host'], SECRET['port'], timeout=timeout)

        try:
            server.login(SECRET['user'], SECRET['password'])
            server.sendmail(sender, recipients, msg.as_string())
        finally:
            server.close()
