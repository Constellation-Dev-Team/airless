
**unreleased**

**v0.4.0**
- [Feature] Allow defining a custom pubsub publish timeout

**v0.3.0**
- [Refactor] Remove airless dependency limitation

**v0.2.0**
- [Refactor] Set `airless-core` dependency to `<1.0.0`

**v0.1.1**
- [Feature] Default `json.dumps` conversion as `str` when publishing a message to pubsub. For instance, datetime will be converted to str

**v0.1.0**
- [Refactor] Remove `GoogleErrorReprocessOperator` from `airless-google-cloud-core` because it is being moved to `airless-google-cloud-storage`
- [Refactor] Upgrade `airless-core` to version `0.2.1`

**v0.0.5**
- [Feature] Automatically generate git tag when bumpversion is triggered
- [Refactor] Add package name to bumpversion commit message
- [Refactor] Change `pubsub_topic` pattern to `queue_topic`

**v0.0.4**
- [Bugfix] Add dynamic dependencies from `requirements.txt` to `pyproject.toml`
- [Feature] Create a new command to generate automatically a tag to deploy a new package version

**v0.0.3**
- [Refactor] Move all build configurations to `pyproject.toml`
- [Refactor] Remove `__init__.py` from root namespace
- [Refactor] add `__all__` object to reference package classes
- [Refactor] Change linter from `flake8` to `ruff`

**v0.0.2**
- [Feature] Get method `get_config` to new path
- [Feature] Enhance dependencies

**v0.0.1**
- [Feature] Package created

**v0.0.0**
