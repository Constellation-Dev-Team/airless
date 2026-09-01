import pytest
import requests

from unittest.mock import MagicMock, patch

from airless.slack.hook import SlackHook


def build_response(json_body, status_code=200):
    """Builds a mocked `requests.Response` like object.

    Args:
        json_body (dict): Body returned by the `json` method.
        status_code (int): HTTP status code. Defaults to 200.

    Returns:
        MagicMock: The mocked response.
    """
    response = MagicMock(spec=requests.Response)
    response.status_code = status_code
    response.json.return_value = json_body
    response.raise_for_status.return_value = None
    response.text = 'ok'
    return response


@pytest.fixture
def hook():
    """Builds a hook with a bot token already set.

    Returns:
        SlackHook: The configured hook.
    """
    h = SlackHook()
    h.set_token('bot-token')
    return h


class TestHeaders:
    def test_get_headers_signature_unchanged(self, hook):
        with pytest.raises(TypeError):
            hook.get_headers('bot')

    def test_get_headers_returns_bot_token(self, hook):
        assert hook.get_headers() == {'Authorization': 'Bearer bot-token'}

    def test_user_token_defaults_to_none(self):
        assert SlackHook().user_token is None

    def test_get_user_headers_raises_when_unset(self, hook):
        with pytest.raises(Exception, match='user token is not set'):
            hook.get_user_headers()

    def test_get_user_headers_returns_user_token(self, hook):
        hook.set_user_token('user-token')
        assert hook.get_user_headers() == {'Authorization': 'Bearer user-token'}


class TestProcessResponse:
    def test_returns_three_tuple_with_cursor(self, hook):
        response = build_response(
            {
                'ok': True,
                'messages': [{'ts': '1'}],
                'response_metadata': {'next_cursor': 'abc'},
            }
        )
        response_json, has_any, next_cursor = hook.process_response(
            response, 'messages'
        )
        assert response_json['messages'] == [{'ts': '1'}]
        assert has_any is True
        assert next_cursor == 'abc'

    def test_empty_cursor_becomes_none(self, hook):
        response = build_response(
            {'ok': True, 'messages': [], 'response_metadata': {'next_cursor': ''}}
        )
        _, has_any, next_cursor = hook.process_response(response, 'messages')
        assert has_any is False
        assert next_cursor is None

    def test_has_any_is_none_without_objs_key(self, hook):
        response = build_response({'ok': True})
        response_json, has_any, next_cursor = hook.process_response(response)
        assert response_json == {'ok': True}
        assert has_any is None
        assert next_cursor is None

    def test_raises_when_not_ok(self, hook):
        response = build_response({'ok': False, 'error': 'not_in_channel'})
        with pytest.raises(Exception, match='Slack error not_in_channel'):
            hook.process_response(response, 'messages')

    def test_raises_http_error(self, hook):
        response = build_response({'ok': True, 'messages': []})
        response.raise_for_status.side_effect = requests.HTTPError('boom')
        with pytest.raises(requests.HTTPError):
            hook.process_response(response, 'messages')

    def test_sleeps_on_too_many_requests(self, hook):
        response = build_response({'ok': True, 'messages': []}, status_code=429)
        with patch('airless.slack.hook.slack.sleep') as mock_sleep:
            hook.process_response(response, 'messages')
        mock_sleep.assert_called_once_with(60)


class TestGetMessages:
    def test_sends_expected_params(self, hook):
        response = build_response({'ok': True, 'messages': [{'ts': '1'}]})
        with patch(
            'airless.slack.hook.slack.requests.get', return_value=response
        ) as mock_get:
            response_json, has_any, next_cursor = hook.get_messages('C123')

        args, kwargs = mock_get.call_args
        assert args[0] == 'https://slack.com/api/conversations.history'
        assert kwargs['headers'] == {'Authorization': 'Bearer bot-token'}
        assert kwargs['params'] == {'channel': 'C123', 'limit': 1000}
        assert response_json['messages'] == [{'ts': '1'}]
        assert has_any is True
        assert next_cursor is None

    def test_sends_cursor_and_timedelta_params(self, hook):
        response = build_response({'ok': True, 'messages': []})
        with patch(
            'airless.slack.hook.slack.requests.get', return_value=response
        ) as mock_get:
            hook.get_messages(
                'C123',
                limit=50,
                timedelta_start=-7,
                timedelta_end=-1,
                cursor='next-page',
            )

        params = mock_get.call_args.kwargs['params']
        assert params['channel'] == 'C123'
        assert params['limit'] == 50
        assert params['cursor'] == 'next-page'
        assert params['oldest'] < params['latest']

    def test_pagination_follows_cursor(self, hook):
        first = build_response(
            {
                'ok': True,
                'messages': [{'ts': '1'}],
                'response_metadata': {'next_cursor': 'page2'},
            }
        )
        second = build_response({'ok': True, 'messages': [{'ts': '2'}]})
        with patch(
            'airless.slack.hook.slack.requests.get', side_effect=[first, second]
        ) as mock_get:
            _, _, cursor = hook.get_messages('C123')
            assert cursor == 'page2'
            _, _, cursor = hook.get_messages('C123', cursor=cursor)
            assert cursor is None

        assert mock_get.call_count == 2
        assert 'cursor' not in mock_get.call_args_list[0].kwargs['params']
        assert mock_get.call_args_list[1].kwargs['params']['cursor'] == 'page2'


class TestGetMessageReplies:
    def test_sends_expected_params(self, hook):
        response = build_response({'ok': True, 'messages': [{'ts': '1.1'}]})
        with patch(
            'airless.slack.hook.slack.requests.get', return_value=response
        ) as mock_get:
            _, has_any, _ = hook.get_message_replies('C123', '1.0', limit=10)

        args, kwargs = mock_get.call_args
        assert args[0] == 'https://slack.com/api/conversations.replies'
        assert kwargs['params'] == {'channel': 'C123', 'ts': '1.0', 'limit': 10}
        assert has_any is True

    def test_sends_timedelta_params(self, hook):
        response = build_response({'ok': True, 'messages': []})
        with patch(
            'airless.slack.hook.slack.requests.get', return_value=response
        ) as mock_get:
            hook.get_message_replies(
                'C123', '1.0', timedelta_start=-2, timedelta_end=-1
            )

        params = mock_get.call_args.kwargs['params']
        assert 'oldest' in params
        assert 'latest' in params


class TestOtherReadMethods:
    def test_get_users(self, hook):
        response = build_response({'ok': True, 'members': [{'id': 'U1'}]})
        with patch(
            'airless.slack.hook.slack.requests.get', return_value=response
        ) as mock_get:
            _, has_any, _ = hook.get_users(limit=10, cursor='c')

        assert mock_get.call_args[0][0] == 'https://slack.com/api/users.list'
        assert mock_get.call_args.kwargs['params'] == {'limit': 10, 'cursor': 'c'}
        assert has_any is True

    def test_get_channels_default_types(self, hook):
        response = build_response({'ok': True, 'channels': []})
        with patch(
            'airless.slack.hook.slack.requests.get', return_value=response
        ) as mock_get:
            hook.get_channels()

        params = mock_get.call_args.kwargs['params']
        assert params['types'] == 'public_channel,private_channel'
        assert params['exclude_archived'] is True

    def test_get_channel(self, hook):
        response = build_response({'ok': True, 'channel': {'id': 'C1'}})
        with patch(
            'airless.slack.hook.slack.requests.get', return_value=response
        ) as mock_get:
            result = hook.get_channel('C1')

        assert mock_get.call_args[0][0] == 'https://slack.com/api/conversations.info'
        assert mock_get.call_args.kwargs['params'] == {'channel': 'C1'}
        assert result == {'ok': True, 'channel': {'id': 'C1'}}

    def test_get_channel_users(self, hook):
        response = build_response({'ok': True, 'members': ['U1']})
        with patch(
            'airless.slack.hook.slack.requests.get', return_value=response
        ) as mock_get:
            _, has_any, _ = hook.get_channel_users('C1')

        assert mock_get.call_args[0][0] == 'https://slack.com/api/conversations.members'
        assert has_any is True

    def test_join_channel(self, hook):
        response = build_response({'ok': True, 'channel': {'id': 'C1'}})
        with patch(
            'airless.slack.hook.slack.requests.post', return_value=response
        ) as mock_post:
            result = hook.join_channel('C1')

        assert mock_post.call_args[0][0] == 'https://slack.com/api/conversations.join'
        assert result['ok'] is True

    def test_join_channel_raises_when_not_ok(self, hook):
        response = build_response({'ok': False, 'error': 'missing_scope'})
        with patch('airless.slack.hook.slack.requests.post', return_value=response):
            with pytest.raises(Exception, match='missing_scope'):
                hook.join_channel('C1')

    def test_search_uses_user_headers(self, hook):
        hook.set_user_token('user-token')
        response = build_response({'ok': True, 'messages': {'matches': []}})
        with patch(
            'airless.slack.hook.slack.requests.get', return_value=response
        ) as mock_get:
            result = hook.search('hello')

        assert mock_get.call_args[0][0] == 'https://slack.com/api/search.messages'
        assert mock_get.call_args.kwargs['headers'] == {
            'Authorization': 'Bearer user-token'
        }
        assert mock_get.call_args.kwargs['params']['query'] == 'hello'
        assert result['ok'] is True

    def test_search_raises_without_user_token(self, hook):
        with patch('airless.slack.hook.slack.requests.get') as mock_get:
            with pytest.raises(Exception, match='user token is not set'):
                hook.search('hello')
        mock_get.assert_not_called()


class TestRegressionWriteMethods:
    def test_send_message_to_channel(self, hook):
        response = build_response({'ok': True, 'ts': '1.0'})
        with patch(
            'airless.slack.hook.slack.requests.post', return_value=response
        ) as mock_post:
            result = hook.send(channel='C1', message='hi')

        assert mock_post.call_args[0][0] == 'https://slack.com/api/chat.postMessage'
        assert mock_post.call_args.kwargs['json'] == {'channel': 'C1', 'text': 'hi'}
        assert mock_post.call_args.kwargs['headers'] == {
            'Authorization': 'Bearer bot-token'
        }
        assert result == {'ok': True, 'ts': '1.0'}

    def test_send_truncates_long_message(self, hook):
        response = build_response({'ok': True})
        with patch(
            'airless.slack.hook.slack.requests.post', return_value=response
        ) as mock_post:
            hook.send(channel='C1', message='a' * 4000)

        assert len(mock_post.call_args.kwargs['json']['text']) == 3000

    def test_send_to_response_url_returns_text(self, hook):
        response = build_response({'ok': True})
        with patch(
            'airless.slack.hook.slack.requests.post', return_value=response
        ) as mock_post:
            result = hook.send(message='hi', response_url='https://hooks.slack.com/x')

        assert mock_post.call_args[0][0] == 'https://hooks.slack.com/x'
        assert result == {'status': 'ok'}

    def test_send_raises_when_not_ok(self, hook):
        response = build_response({'ok': False, 'error': 'channel_not_found'})
        with patch('airless.slack.hook.slack.requests.post', return_value=response):
            with pytest.raises(Exception, match='channel_not_found'):
                hook.send(channel='C1', message='hi')

    def test_react(self, hook):
        response = build_response({'ok': True})
        with patch(
            'airless.slack.hook.slack.requests.post', return_value=response
        ) as mock_post:
            result = hook.react('C1', 'thumbsup', '1.0')

        assert mock_post.call_args[0][0] == 'https://slack.com/api/reactions.add'
        assert mock_post.call_args.kwargs['json'] == {
            'channel': 'C1',
            'name': 'thumbsup',
            'timestamp': '1.0',
        }
        assert result == {'ok': True}

    def test_react_raises_when_not_ok(self, hook):
        response = build_response({'ok': False, 'error': 'already_reacted'})
        with patch('airless.slack.hook.slack.requests.post', return_value=response):
            with pytest.raises(Exception, match='already_reacted'):
                hook.react('C1', 'thumbsup', '1.0')

    def test_get_user_id_by_email(self, hook):
        response = build_response({'ok': True, 'user': {'id': 'U9'}})
        with patch(
            'airless.slack.hook.slack.requests.get', return_value=response
        ) as mock_get:
            assert hook.get_user_id_by_email('a@b.com') == 'U9'

        assert mock_get.call_args[0][0] == 'https://slack.com/api/users.lookupByEmail'
