
from typing import Any, Dict, List, Optional

from airless.core.operator import BaseEventOperator
from airless.core.hook import SecretManagerHook
from airless.core.utils import get_config

from airless.slack.hook import SlackHook


class SlackSendOperator(BaseEventOperator):
    """Operator for sending messages to Slack."""

    def __init__(self) -> None:
        """Initializes the SlackSendOperator."""
        super().__init__()
        self.slack_hook = SlackHook()
        self.secret_manager_hook = SecretManagerHook()

    def execute(self, data: Dict[str, Any], topic: str) -> None:
        """Executes the sending of messages to Slack.

        Args:
            data (Dict[str, Any]): The data containing message information.
                `channels` accepts channel IDs and/or user IDs (Slack opens a DM
                automatically for user IDs). `user_emails` resolves each email to a
                Slack user ID before sending a DM.
            topic (str): The Pub/Sub topic.
        """
        channels: List[str] = data.get('channels', [])
        user_emails: List[str] = data.get('user_emails', [])
        secret_id: str = data.get('secret_id', 'slack_alert')
        message: str = data.get('message')
        blocks: Optional[List[Dict[str, Any]]] = data.get('blocks')
        attachments: Optional[List[Dict[str, Any]]] = data.get('attachments')
        thread_ts: Optional[str] = data.get('thread_ts')
        reply_broadcast: bool = data.get('reply_broadcast', False)
        response_url: Optional[str] = data.get('response_url')
        response_type: Optional[str] = data.get('response_type')
        replace_original: Optional[bool] = data.get('replace_original')

        token: str = self.secret_manager_hook.get_secret(get_config('GCP_PROJECT'), secret_id, True)['bot_token']
        self.slack_hook.set_token(token)

        if not channels and not user_emails and not response_url:
            raise Exception('Either channels, user_emails or response_url must be set')

        recipients = set(channels)
        for email in user_emails:
            try:
                recipients.add(self.slack_hook.get_user_id_by_email(email))
            except Exception as e:
                self.logger.error(f"Failed to resolve Slack user by email '{email}': {e}")

        for channel in recipients:
            response = self.slack_hook.send(
                channel=channel,
                message=message,
                blocks=blocks,
                thread_ts=thread_ts,
                reply_broadcast=reply_broadcast,
                attachments=attachments,
                response_type=response_type,
                replace_original=replace_original)
            self.logger.debug(response)

        if response_url:
            response = self.slack_hook.send(
                message=message,
                blocks=blocks,
                thread_ts=thread_ts,
                reply_broadcast=reply_broadcast,
                attachments=attachments,
                response_url=response_url,
                response_type=response_type,
                replace_original=replace_original)
            self.logger.debug(response)


class SlackReactOperator(BaseEventOperator):
    """Operator for reacting to Slack messages."""

    def __init__(self) -> None:
        """Initializes the SlackReactOperator."""
        super().__init__()
        self.slack_hook = SlackHook()
        self.secret_manager_hook = SecretManagerHook()

    def execute(self, data: Dict[str, Any], topic: str) -> None:
        """Executes the reaction to a Slack message.

        Args:
            data (Dict[str, Any]): The data containing reaction information.
            topic (str): The Pub/Sub topic.
        """
        channel: str = data['channel']
        secret_id: str = data.get('secret_id', 'slack_alert')
        reaction: str = data.get('reaction')
        ts: str = data.get('ts')

        token: str = self.secret_manager_hook.get_secret(get_config('GCP_PROJECT'), secret_id, True)['bot_token']
        self.slack_hook.set_token(token)

        response = self.slack_hook.react(channel, reaction, ts)
        self.logger.debug(response)
