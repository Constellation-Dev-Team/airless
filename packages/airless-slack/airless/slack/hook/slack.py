import requests

from datetime import datetime, timedelta
from time import sleep
from typing import Any, Dict, List, Optional, Tuple, Union

from airless.core.hook import BaseHook


class SlackHook(BaseHook):
    """Hook for interacting with Slack API."""

    def __init__(self) -> None:
        """Initializes the SlackHook."""
        super().__init__()
        self.api_url: str = 'slack.com'
        self.user_token: Optional[str] = None

    def set_token(self, token: str) -> None:
        """Sets the authorization token for the Slack API.

        Args:
            token (str): The authorization token.
        """
        self.token = token

    def set_user_token(self, token: str) -> None:
        """Sets the user authorization token for the Slack API.

        Some Slack endpoints, such as `search.messages`, only accept a user
        token instead of a bot token.

        Args:
            token (str): The user authorization token.
        """
        self.user_token = token

    def get_headers(self) -> Dict[str, str]:
        """Gets the headers for the Slack API requests.

        Returns:
            Dict[str, str]: The headers including the authorization token.
        """
        return {'Authorization': f'Bearer {self.token}'}

    def get_user_headers(self) -> Dict[str, str]:
        """Gets the headers for Slack API requests that require a user token.

        Returns:
            Dict[str, str]: The headers including the user authorization token.

        Raises:
            Exception: When the user token was not set with `set_user_token`.
        """
        if not self.user_token:
            raise Exception(
                'Slack user token is not set. Call set_user_token before using '
                'endpoints that require a user token'
            )
        return {'Authorization': f'Bearer {self.user_token}'}

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

    def process_response(
        self, response: requests.Response, objs_key: Optional[str] = None
    ) -> Tuple[Dict[str, Any], Optional[bool], Optional[str]]:
        """Validates a Slack API response and extracts its payload.

        Waits 60 seconds on rate-limit (429) responses and then raises on HTTP
        errors or when the Slack response body contains `ok: false`, so the
        caller fails normally and the event can be retried.

        Args:
            response (requests.Response): The HTTP response from the Slack API.
            objs_key (Optional[str]): Key in the response JSON whose list length
                determines `has_any`. Pass None to skip the check.

        Returns:
            Tuple[Dict[str, Any], Optional[bool], Optional[str]]: A 3-tuple of:
                - The full JSON response body.
                - True if the list at `objs_key` is non-empty, or None when
                  `objs_key` is not provided.
                - Pagination cursor for the next page, or None.

        Raises:
            requests.HTTPError: When the HTTP status code indicates an error.
            Exception: When the Slack response body contains `ok: false`.
        """
        if response.status_code == requests.codes.too_many_requests:
            sleep(60)

        response.raise_for_status()
        response_json = response.json()

        if not response_json['ok']:
            raise Exception(f'Slack error {response_json["error"]}')

        has_any = len(response_json[objs_key]) > 0 if objs_key else None
        next_cursor = response_json.get('response_metadata', {}).get('next_cursor')
        if not next_cursor:
            next_cursor = None
        return response_json, has_any, next_cursor

    def timedelta_to_timestamp(self, _timedelta: Union[int, float]) -> float:
        """Converts a day offset relative to now into a Unix timestamp.

        Args:
            _timedelta (Union[int, float]): Number of days to add to the current
                time (use negative values for past dates).

        Returns:
            float: Unix timestamp for the resulting datetime.
        """
        return (datetime.now() + timedelta(days=_timedelta)).timestamp()

    def get_users(
        self, limit: int = 1000, cursor: Optional[str] = None
    ) -> Tuple[Dict[str, Any], Optional[bool], Optional[str]]:
        """Fetches a paginated list of workspace users.

        Args:
            limit (int): Maximum number of users to return per page. Defaults to 1000.
            cursor (Optional[str]): Pagination cursor from a previous response.

        Returns:
            Tuple[Dict[str, Any], Optional[bool], Optional[str]]: Result from
                `process_response` with key 'members'.
        """
        params: Dict[str, Any] = {'limit': limit}
        if cursor:
            params['cursor'] = cursor

        response = requests.get(
            f'https://{self.api_url}/api/users.list',
            headers=self.get_headers(),
            params=params,
            timeout=10,
        )
        return self.process_response(response, 'members')

    def get_channels(
        self,
        limit: int = 1000,
        cursor: Optional[str] = None,
        types: Optional[str] = None,
        exclude_archived: bool = True,
    ) -> Tuple[Dict[str, Any], Optional[bool], Optional[str]]:
        """Fetches a paginated list of workspace channels.

        Private channels are only returned when the bot is a member of them, so
        listing already acts as an access filter for them.

        Args:
            limit (int): Maximum number of channels to return per page. Defaults to 1000.
            cursor (Optional[str]): Pagination cursor from a previous response.
            types (Optional[str]): Comma separated conversation types to list.
                Defaults to 'public_channel,private_channel'.
            exclude_archived (bool): Whether to skip archived channels, which
                never have new messages. Defaults to True.

        Returns:
            Tuple[Dict[str, Any], Optional[bool], Optional[str]]: Result from
                `process_response` with key 'channels'.
        """
        params: Dict[str, Any] = {
            'limit': limit,
            'types': types or 'public_channel,private_channel',
            'exclude_archived': exclude_archived,
        }
        if cursor:
            params['cursor'] = cursor

        response = requests.get(
            f'https://{self.api_url}/api/conversations.list',
            headers=self.get_headers(),
            params=params,
            timeout=10,
        )
        return self.process_response(response, 'channels')

    def get_channel(self, id: str) -> Dict[str, Any]:
        """Fetches metadata for a single channel.

        Args:
            id (str): The Slack channel ID.

        Returns:
            Dict[str, Any]: The full JSON response body from conversations.info.

        Raises:
            requests.HTTPError: When the HTTP status code indicates an error.
        """
        params: Dict[str, Any] = {'channel': id}

        response = requests.get(
            f'https://{self.api_url}/api/conversations.info',
            headers=self.get_headers(),
            params=params,
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def get_channel_users(
        self, channel_id: str, limit: int = 1000, cursor: Optional[str] = None
    ) -> Tuple[Dict[str, Any], Optional[bool], Optional[str]]:
        """Fetches a paginated list of member IDs for a channel.

        Args:
            channel_id (str): The Slack channel ID.
            limit (int): Maximum number of members to return per page. Defaults to 1000.
            cursor (Optional[str]): Pagination cursor from a previous response.

        Returns:
            Tuple[Dict[str, Any], Optional[bool], Optional[str]]: Result from
                `process_response` with key 'members'.
        """
        params: Dict[str, Any] = {'limit': limit, 'channel': channel_id}
        if cursor:
            params['cursor'] = cursor

        response = requests.get(
            f'https://{self.api_url}/api/conversations.members',
            headers=self.get_headers(),
            params=params,
            timeout=10,
        )
        return self.process_response(response, 'members')

    def join_channel(self, channel_id: str) -> Dict[str, Any]:
        """Adds the bot to a public channel before reading its history.

        Raises on failure (e.g. missing scope or rate-limited) so the caller
        fails normally and the event can be retried.

        Args:
            channel_id (str): The Slack channel ID to join.

        Returns:
            Dict[str, Any]: The full JSON response body from conversations.join.

        Raises:
            requests.HTTPError: When the HTTP status code indicates an error.
            Exception: When the Slack response body contains `ok: false`.
        """
        params: Dict[str, Any] = {'channel': channel_id}

        response = requests.post(
            f'https://{self.api_url}/api/conversations.join',
            headers=self.get_headers(),
            params=params,
            timeout=10,
        )
        response.raise_for_status()
        response_json = response.json()
        if not response_json['ok']:
            raise Exception(
                f'When trying to join the channel {channel_id}, '
                f'Slack gave this error: {response_json["error"]}'
            )
        return response_json

    def get_messages(
        self,
        channel_id: str,
        limit: int = 1000,
        timedelta_start: Optional[Union[int, float]] = None,
        timedelta_end: Optional[Union[int, float]] = None,
        cursor: Optional[str] = None,
    ) -> Tuple[Dict[str, Any], Optional[bool], Optional[str]]:
        """Fetches a paginated list of messages from a channel history.

        Args:
            channel_id (str): The Slack channel ID.
            limit (int): Maximum number of messages to return per page. Defaults to 1000.
            timedelta_start (Optional[Union[int, float]]): Day offset from now for
                the oldest message boundary. Defaults to None (no lower bound).
            timedelta_end (Optional[Union[int, float]]): Day offset from now for
                the latest message boundary. Defaults to None (no upper bound).
            cursor (Optional[str]): Pagination cursor from a previous response.

        Returns:
            Tuple[Dict[str, Any], Optional[bool], Optional[str]]: Result from
                `process_response` with key 'messages'.
        """
        params: Dict[str, Any] = {'channel': channel_id, 'limit': limit}
        if timedelta_start:
            params['oldest'] = self.timedelta_to_timestamp(timedelta_start)
        if timedelta_end:
            params['latest'] = self.timedelta_to_timestamp(timedelta_end)
        if cursor:
            params['cursor'] = cursor

        response = requests.get(
            f'https://{self.api_url}/api/conversations.history',
            headers=self.get_headers(),
            params=params,
            timeout=10,
        )
        return self.process_response(response, 'messages')

    def get_message_replies(
        self,
        channel_id: str,
        message_ts: str,
        limit: int = 1000,
        timedelta_start: Optional[Union[int, float]] = None,
        timedelta_end: Optional[Union[int, float]] = None,
        cursor: Optional[str] = None,
    ) -> Tuple[Dict[str, Any], Optional[bool], Optional[str]]:
        """Fetches a paginated list of replies for a thread.

        Args:
            channel_id (str): The Slack channel ID containing the thread.
            message_ts (str): The timestamp of the parent message that started
                the thread.
            limit (int): Maximum number of replies to return per page. Defaults to 1000.
            timedelta_start (Optional[Union[int, float]]): Day offset from now for
                the oldest reply boundary. Defaults to None (no lower bound).
            timedelta_end (Optional[Union[int, float]]): Day offset from now for
                the latest reply boundary. Defaults to None (no upper bound).
            cursor (Optional[str]): Pagination cursor from a previous response.

        Returns:
            Tuple[Dict[str, Any], Optional[bool], Optional[str]]: Result from
                `process_response` with key 'messages'.
        """
        params: Dict[str, Any] = {
            'channel': channel_id,
            'ts': message_ts,
            'limit': limit,
        }
        if timedelta_start:
            params['oldest'] = self.timedelta_to_timestamp(timedelta_start)
        if timedelta_end:
            params['latest'] = self.timedelta_to_timestamp(timedelta_end)
        if cursor:
            params['cursor'] = cursor

        response = requests.get(
            f'https://{self.api_url}/api/conversations.replies',
            headers=self.get_headers(),
            params=params,
            timeout=10,
        )
        return self.process_response(response, 'messages')

    def search(
        self,
        query: str,
        sort: str = 'timestamp',
        sort_dir: str = 'desc',
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """Searches messages across the workspace using the user token.

        Args:
            query (str): The search query string.
            sort (str): Field to sort results by. Defaults to 'timestamp'.
            sort_dir (str): Sort direction, either 'asc' or 'desc'. Defaults to 'desc'.
            page (int): Page number to retrieve. Defaults to 1.
            page_size (int): Number of results per page. Defaults to 20.

        Returns:
            Dict[str, Any]: The full JSON response body from search.messages.

        Raises:
            requests.HTTPError: When the HTTP status code indicates an error.
            Exception: When the user token was not set with `set_user_token`.
        """
        params: Dict[str, Any] = {
            'query': query,
            'sort': sort,
            'sort_dir': sort_dir,
            'page': page,
            'count': page_size,
        }
        response = requests.get(
            f'https://{self.api_url}/api/search.messages',
            headers=self.get_user_headers(),
            params=params,
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
