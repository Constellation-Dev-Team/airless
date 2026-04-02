
**unreleased**
- [Feature] Allow the file name from the download file to be manually overriden in `FileHook`

**v0.4.1**
- [Bugfix] Fix topic name to `QUEUE_TOPIC_BATCH_WRITE_PROCESS`

**v0.4.0**
- [Refactor] Remove airless dependency limitation

**v0.3.0**
- [Refactor] Set `airless-google-cloud-core` dependency to `<1.0.0`
- [Refactor] Set `airless-core` dependency to `<1.0.0`

**v0.2.0**
- [Refactor] Allow `airless-core<0.4.0` to work with `airless-google-cloud-storage`

**v0.1.2**
- [Bugfix] Update to `airless-core===0.2.5` because event id was being set as string when it should be an int

**v0.1.1**
- [Refactor] Write parquet to local file before uploading to GCS because it requires less memory
- [Feature] Always release unused memory from pyarrow to avoid a memory leak
- [Refactor] Force parquet schema when creating the parquet table instead of casting it after in order to use less memory

**v0.1.0**
- [Bugfix] Rollback Google Cloud Storage Operators that were mistakenly deleted
- [Feature] Create `GoogleErrorReprocessOperator` that was previously in `airless-google-cloud-core` package and now was moved to `airless-google-cloud-storage` in order to be able to save error data directly to datalake

**v0.0.8**
- [Bugfix] GCS hook does not have a `read` function anymore, it was changed to `read_as_string`

**v0.0.7**
- [Bugfix] Add dynamic dependencies from `requirements.txt` to `pyproject.toml`
- [Feature] Create a new command to generate automatically a tag to deploy a new package version
- [Feature] Automatically generate git tag when bumpversion is triggered
- [Refactor] Add package name to bumpversion commit message

**v0.0.6**
- [Refactor] Use [`deprecation`](https://pypi.org/project/deprecation/) to deprecate functions instead of custom decorator
- [Refactor] Schedule deprecation for `BatchWriteProcessOperator` to version `1.0.0`
- [Refactor] Move all build configurations to `pyproject.toml`
- [Refactor] Remove `__init__.py` from root namespace
- [Refactor] add `__all__` object to reference package classes
- [Refactor] Change linter from `flake8` to `ruff`

**v0.0.5**
- [Feature] Change some methods in `GcsHook` to support `**kwargs` arguments

**v0.0.4**
- [Feature] Get method `get_config` to new path
- [Feature] Enhance dependencies

**v0.0.3**
- [Bugfix] Add `airless-google-cloud-core` as a dependency

**v0.0.2**
- [Feature] Add method `read_as_bytes` to `GcsHook` class
- [Change] Change method `read` from `GcsHook` class to `read_as_string`

**v0.0.1**
- [Feature] Package created

**v0.0.0**
