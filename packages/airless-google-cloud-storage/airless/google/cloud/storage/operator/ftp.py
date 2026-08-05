import os
from typing import Dict

from airless.core.hook import FtpHook
from airless.google.cloud.storage.operator import FileUrlToGcsOperator


class FtpToGcsOperator(FileUrlToGcsOperator):
    """Operator for transferring files from FTP to GCS."""

    def __init__(self) -> None:
        """Initializes the FtpToGcsOperator."""
        super().__init__()
        self.ftp_hook = FtpHook()

    def execute(self, data: Dict[str, str], topic: str) -> None:
        """Executes the FTP to GCS transfer.

        Args:
            data (Dict[str, str]): The data containing FTP and GCS information.
            topic (str): The Pub/Sub topic.
        """
        origin = data['origin']
        destination = data['destination']

        self.ftp_hook = FtpHook()
        self.ftp_hook.login(origin['host'], origin.get('user'), origin.get('pass'))

        local_filepath = self.ftp_hook.download(origin['directory'], origin['filename'])

        local_filepath = self.move_to_destinations(local_filepath, destination)

        os.remove(local_filepath)
