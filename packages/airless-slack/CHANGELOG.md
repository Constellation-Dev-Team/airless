
**unreleased**
- [Feature] Add Slack channel read methods to `SlackHook`: `get_users`, `get_channels`, `get_channel`, `get_channel_users`, `join_channel`, `get_messages`, `get_message_replies` and `search`
- [Feature] Add `process_response` and `timedelta_to_timestamp` helpers to `SlackHook`
- [Feature] Add user token support to `SlackHook` via `set_user_token` and `get_user_headers`, used by `search`
- [Feature] Add unit tests for `SlackHook` read and write methods
- [Bugfix] Accept a day offset of `0` in `get_messages` and `get_message_replies`, raise on Slack `ok: false` responses in `get_channel` and `search`, and send `exclude_archived` as a lowercase string in `get_channels`

**v0.4.3**
- [Bugfix] check api response only when not responding to a thread

**v0.4.2**
- [Bugfix] Raise exception when message cannot be sent to slack
- [Bugfix] Raise exception when react to message cannot be sent to slack

**v0.4.1**
- [Bugfix] Guard against `None` values for `channels`/`user_emails`, dedupe `user_emails` before lookup, and use safe dict access on the Slack `users.lookupByEmail` response

**v0.4.0**
- [Feature] Support sending messages to users (DM) via user ID (in `channels`) or `user_emails`

**v0.3.0**
- [Refactor] Remove airless dependency limitation

**v0.2.0**
- [Refactor] Set `airless-core` dependency to `<1.0.0`
- [Refactor] Set `airless-google-cloud-core` dependency to `<1.0.0`
- [Refactor] Set `airless-google-cloud-secret-manager` dependency to `<1.0.0`

**v0.1.1**
- [Bugfix] Refactor Google operators to inherit from `GoogleBaseEventOperator`, ensuring proper error handling and consistent use of the `queue_hook` attribute

**v0.1.0**
- [Refactor] Update requirements.txt to get new `airless-core` version `0.2.1`

**v0.0.5**
- [Bugfix] Add `GCP_PROJECT` param to secret manager get_secret calls

**v0.0.4**
- [Bugfix] Add dynamic dependencies from `requirements.txt` to `pyproject.toml`
- [Feature] Create a new command to generate automatically a tag to deploy a new package version
- [Feature] Automatically generate git tag when bumpversion is triggered
- [Refactor] Add package name to bumpversion commit message

**v0.0.3**
- [Refactor] Move all build configurations to `pyproject.toml`
- [Refactor] Remove `__init__.py` from root namespace
- [Refactor] add `__all__` object to reference package classes
- [Refactor] Change linter from `flake8` to `ruff`

**v0.0.2**
- [Feature] Enhance dependencies

**v0.0.1**
- [Feature] Package created

**v0.0.0**
