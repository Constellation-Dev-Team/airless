
**unreleased**
- [Feature] Allow the file name from the download file to be manually overriden in `FileHook`
- [Enhancement] Use the final URL (after redirects) to dinamically create the file name when downloading a new file

**v0.4.2**
- [Bugfix] Rollback `BaseDto` which is still in use by `PubsubToBigqueryOperator`

**v0.4.1**
* [Refactor] Remove dependency from `cgi` because it is being deprecated in python 3.13

**v0.4.0**
- [Feature] Get `filename` when downloading a file from the `Content-Disposition` header

**v0.3.1**
- [Bugfix] Remove attachment type and always attach the file to email as binary

**v0.3.0**
- [Bugfix] Aligned `message_id` and `event_id` to be `int` type.
- [Bugfix] Send email body even when the email has an attachment

**v0.2.6**
- [Feature] Force a serialization as string when sending data to datalake for data types json does not know how to serialize, f.i. datetime

**v0.2.5**
- [Bugfix] Force event id to be an integer

**v0.2.4**
- [Refactor] Do not convert datetime to string when preparing rows to store in datalake
- [Refactor] Force a serialization as string for data types json does not know how to serialize, f.i. datetime

**v0.2.3**
- [Feature] Do not try to reprocess error from the error function to avoid an infinite loop
- [Refactor] If error, email or slack operator project env vars are not set, defaults to the function project, which must be set by the queue hook implementation

**v0.2.2**
- [Bugfix] Set error operator project as env var

**v0.2.1**
- [Feature] Add methods to `DatalakeHook` to normalize data before storing to datalake

**v0.2.0**
- [Deprecation] Remove deprecated class `BaseDto`
- [Feature] `ErrorReprocessOperator` now sends error data directly to datalake instead of sending to another topic, so another operator can send to the datalake

**v0.1.5**
- [Feature] Create a new command to generate automatically a tag to deploy a new package version
- [Feature] Automatically generate git tag when bumpversion is triggered
- [Refactor] Add package name to bumpversion commit message
- [Bugfix] Remove `print` from `add_key` method in `RedirectOperator`

**v0.1.4**
- [Bugfix] Add dynamic dependencies from `requirements.txt` to `pyproject.toml`

**v0.1.3**
- [Refactor] Remove references to cloud-specific products in `README.md` 
- [Feature] Add unit tests for the utils functions
- [Refactor] Deprecate `BaseDto`
- [Refactor] Use [`deprecation`](https://pypi.org/project/deprecation/) to deprecate functions instead of custom decorator
- [Refactor] Remove `__init__.py` from root namespace
- [Refactor] Move all build configurations to `pyproject.toml`
- [Refactor] add `__all__` object to reference package classes
- [Refactor] Change linter from `flake8` to `ruff`

**v0.1.2**
- [Feature] Add support to `FileHook` write binary data
- [Feature] Change some methods in `FileHook` to support `**kwargs` arguments

**v0.1.1**
- [Feature] Add new utils `enum` that have `baseEnum` class for basic list of objects selection class
- [Feature] Add `BaseLLMHook` to interact with LLMs
- [Feature] Change `config.py` from `airless` root to `utils` folder, for enhance the package structure
- [Feature] Enhance dependencies

**v0.1.0**
- [Feature] Split modules into new packages

**v0.0.73**
- [Feature] Update `bigquery` package

**v0.0.72**
- [Feature] Return target filename after uploading data to GCS

**v0.0.71**
- [Feature] Allow file url to gcs operator to save file to a date partitioned directory structure

**v0.0.70**
- [Feature] Add namespace in setuptools

**v0.0.69**
- [Refactor] Remove old batch detect/aggregate functions
- [Feature] Add new service base class
- [Feature] Create deprecated decorators

**v0.0.68**
- [Feature] Return custom http response from operator
- [Feature] Do not execute next tasks if an error was thrown

**v0.0.67**
- [Refactor] Change GCS batch size to 100

**v0.0.66**
- [Refactor] Rewrite logic `BatchWriteDetectAggregateOperator` to be more clear
- [Feature] Write tests for `BatchWriteDetectAggregateOperator`

**v0.0.65**
- [Feature] Allow slack hook and operator to use parameters `response_url`, `response_type` and `replace_original`

**v0.0.64**
- [Feature] Add new parameter to process all files in bucket

**v0.0.63**
- [Feature] Allow email operator to use different SMTP secrets according to an env var

**v0.0.62**
- [Bugfix] Change directory from key to directory because key is the used in the previous for statement, directory is the current for statement

**v0.0.61**
- [Feature] Move files in `GcsHook` using batch operations to copy and delete files in order to improve performance
- [Feature] Add random hash to filename to increase upload velocity
- [Feature] Add logic to control which file timestamps are being processed

**v0.0.60**
- [Bugfix] In `BatchWriteProcessParquetOperator` change `send_to_processed_move` to use redirect function
- [Feature] Add `BatchAggregateParquetFilesOperator` class to agregate parquet files
- [Feature] Add `BatchWriteDetectAggregateOperator` class to compare file sizes and trigger `BatchAggregateParquetFilesOperator`
- [Feature] Change `send_to_landing_zone` to write parquet direct to gcs raw zone when `time_partition` is defined
- [Feature] Remove `BatchWriteDetectSizeOnlyOperator` because will not be used

**v0.0.59**
- [Feature] Add file size scale in `BatchWriteDetectSizeOnlyOperator` to allow processing of larger partitions

**v0.0.58**
- [Feature] Change from `BatchWriteProcessOrcOperator` to `BatchWriteProcessParquetOperator` to use parquet instead of orc

**v0.0.57**
- [Feature] Add support to `BatchWriteProcessOrcOperator` read ndjson

**v0.0.56**
- [Feature] Add partition logic on `send_to_landing_zone`
- [Feature] Remove partition logic from `BatchWriteProcessOrcOperator`

**v0.0.55**
- [Feature] Add the ability to send attachments in a slack message

**v0.0.53**
- [Feature] Create a new write detect operator with name `BatchWriteDetectSizeOnlyOperator` without the validation of the number of files
- [Feature] Create new operator `BatchWriteProcessOrcOperator` that write ORC file format

**v0.0.52**
- [Feature] Allow `BatchWriteDetectOperator` to receive a prefix to process only a few files

**v0.0.51**
- [Feature] Add `options` to method `build_success_message` in class `FileDetectOperator`, to allow pass generic arguments

**v0.0.50**
- [Feature] Add flow to `CONTRIBUTING.md`
- [Bugfix] Set max error timeout to 480 seconds

**v0.0.49**
- [Feature] Add automatically semantic version tags with `bump2version`
- [Feature] Add github action to get tag and publish to pypi
- [Feature] Add `CONTRIBUTING.md` and `CHANGELOG.md`

**Types of changes**
- [Feature]
- [Bugfix]
- [Hotfix]
