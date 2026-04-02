import os
import re
from typing import Dict, List, Union, Any
from datetime import datetime

from airless.core.hook import FileHook
from airless.google.cloud.core.operator import GoogleBaseEventOperator
from airless.google.cloud.storage.hook import GcsHook


class FileUrlToGcsOperator(GoogleBaseEventOperator):
    """Operator for transferring files from a URL to GCS."""

    def __init__(self) -> None:
        """Initializes the FileUrlToGcsOperator."""
        super().__init__()
        self.file_hook = FileHook()
        self.gcs_hook = GcsHook()

    def execute(self, data: Dict[str, Any], topic: str) -> None:
        """Executes the file transfer from URL to GCS.

        Args:
            data (Dict[str, Any]): The data containing URL and GCS information.
            topic (str): The Pub/Sub topic.
        """
        origin = data['origin']
        destination = data['destination']

        local_filepath = self.file_hook.download(
            url=origin['url'],
            headers=origin.get('headers'),
            timeout=origin.get('timeout', 500),
            proxies=origin.get('proxies'),
            override_filename=origin.get('filename'),
        )

        self.move_to_destinations(local_filepath, destination)

        os.remove(local_filepath)

    def move_to_destinations(
        self,
        local_filepath: str,
        destination: Union[Dict[str, Any], List[Dict[str, Any]]],
    ) -> None:
        """Moves the downloaded file to the specified destinations.

        Args:
            local_filepath (str): The local file path.
            destination (Union[Dict[str, Any], List[Dict[str, Any]]]): The destination(s) for the file.
        """
        original_filepath = local_filepath
        destinations = destination if isinstance(destination, list) else [destination]

        for dest in destinations:
            if dest.get('filename'):
                local_filepath = self.file_hook.rename(
                    from_filename=local_filepath, to_filename=dest.get('filename')
                )

            bucket = dest['bucket']
            directory = dest.get(
                'directory',
                f'{dest.get("dataset")}/{dest.get("table")}/{dest.get("mode")}',
            )
            remove_null_byte = dest.get('remove_null_byte')
            regex = dest.get('regex', '.*')
            time_partition = dest.get('time_partition', False)

            if re.search(regex, local_filepath, re.IGNORECASE):
                if remove_null_byte:
                    self.remove_null_byte(local_filepath)
                self.gcs_hook.upload(
                    local_filepath,
                    bucket,
                    directory
                    + (
                        f'/date={datetime.today().strftime("%Y-%m-%d")}'
                        if time_partition
                        else ''
                    ),
                )

                if local_filepath != original_filepath:  # revert to original filename
                    local_filepath = self.file_hook.rename(
                        from_filename=local_filepath, to_filename=original_filepath
                    )

    def remove_null_byte(self, local_filepath: str) -> None:
        """Removes null bytes from the specified file.

        Args:
            local_filepath (str): The local file path.
        """
        splits = local_filepath.split('/')
        tmp_file = '/'.join(splits[:-1] + ['tmp-' + splits[-1]])

        escaped_filepath = re.escape(local_filepath)

        response = os.system(
            f"tr -d '\\000' < {escaped_filepath} > {tmp_file} && mv {tmp_file} {escaped_filepath}"
        )
        if response != 0:
            raise Exception('not able to remove null bytes')
