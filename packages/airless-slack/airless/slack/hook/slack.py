import requests
from typing import Any, Dict, List, Optional

from airless.core.hook import BaseHook


class SlackHook(BaseHook):
    """Hook for interacting with Slack API."""

    def __init__(self) -> None:
        """Initializes the SlackHook."""
        super().__init__()
        self.api_url: str = 'slack.com'

    def set_token(self, token: str) -> None:
        """Sets the authorization token for the Slack API.

        Args:
            token (str): The authorization token.
        """
        self.token = token

    def get_headers(self) -> Dict[str, str]:
        """Gets the headers for the Slack API requests.

        Returns:
            Dict[str, str]: The headers including the authorization token.
        """
        return {'Authorization': f'Bearer {self.token}'}

    def send(
        self,
        channel: Optional[str] = None,
        message: Optional[str] = None,
        blocks: Optional[List[Dict[str, Any]]] = None,
        thread_ts: Optional[str] = None,
        reply_broadcast: bool = False,
        attachments: Optional[List[Dict[str, Any]]] = None,
        response_url: Optional[str] = None,
        response_type: Optional[str] = None,
        replace_original: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Sends a message to a Slack channel or a response URL.

        Args:
            channel (Optional[str]): The channel to send the message to.
            message (Optional[str]): The message text.
            blocks (Optional[List[Dict[str, Any]]]): The message blocks.
            thread_ts (Optional[str]): The timestamp of the thread to reply to.
            reply_broadcast (bool): Whether to broadcast the reply to the channel.
            attachments (Optional[List[Dict[str, Any]]]): The message attachments.
            response_url (Optional[str]): The response URL to send the message to.
            response_type (Optional[str]): The response type.
            replace_original (Optional[bool]): Whether to replace the original message.

        Returns:
            Dict[str, Any]: The response from the Slack API.
        """
        data: Dict[str, Any] = {}

        if channel:
            data['channel'] = channel

        if message:
            message = message[:3000]  # Slack does not accept long messages
            data['text'] = message

        if blocks:
            data['blocks'] = blocks

        if attachments:
            data['attachments'] = attachments

        if thread_ts:
            data['thread_ts'] = thread_ts
            data['reply_broadcast'] = reply_broadcast

        if response_type:
            data['response_type'] = response_type

        if replace_original:
            data['replace_original'] = replace_original

        response = requests.post(
            response_url or f'https://{self.api_url}/api/chat.postMessage',
            headers=self.get_headers(),
            json=data,
            timeout=10,
        )
        response.raise_for_status()

        if response_url:
            return {'status': response.text}

        response_json = response.json()
        if not response_json.get('ok'):
            raise Exception(
                f'Failed to send slack message: {response_json.get("error", "unknown error")}'
            )

        return response.json()

    def get_user_id_by_email(self, email: str) -> str:
        """Resolves a Slack user ID from their email address.

        Args:
            email (str): The user's email address.

        Returns:
            str: The Slack user ID.
        """
        response = requests.get(
            f'https://{self.api_url}/api/users.lookupByEmail',
            headers=self.get_headers(),
            params={'email': email},
            timeout=10,
        )
        response.raise_for_status()
        response_json = response.json()

        if not response_json.get('ok'):
            raise Exception(
                f"Failed to lookup Slack user by email '{email}': {response_json.get('error', 'unknown error')}"
            )

        user_id = (response_json.get('user') or {}).get('id')
        if not user_id:
            raise Exception(
                f"Failed to lookup Slack user by email '{email}': missing user id in response"
            )

        return user_id

    def react(self, channel: str, reaction: str, ts: str) -> Dict[str, Any]:
        """Adds a reaction to a Slack message.

        Args:
            channel (str): The channel of the message.
            reaction (str): The reaction to add.
            ts (str): The timestamp of the message.

        Returns:
            Dict[str, Any]: The response from the Slack API.
        """
        data: Dict[str, Any] = {'channel': channel, 'name': reaction, 'timestamp': ts}
        response = requests.post(
            f'https://{self.api_url}/api/reactions.add',
            headers=self.get_headers(),
            json=data,
            timeout=10,
        )
        response.raise_for_status()
        response_json = response.json()
        if not response_json.get('ok'):
            raise Exception(
                f'Failed to react to message: {response_json.get("error", "unknown error")}'
            )
        return response_json
