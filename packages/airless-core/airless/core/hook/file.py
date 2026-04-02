import json
import ndjson
import os
import requests
import re
import uuid

from datetime import datetime
from dateutil import parser
from ftplib import FTP
from typing import Any, Optional

from airless.core.hook import BaseHook


class FileHook(BaseHook):
    """FileHook class for handling file operations.

    This class provides methods to write data to local files in
    various formats (JSON and NDJSON), download files, rename files,
    and list files in a directory.

    Inherits from:
        BaseHook: The base class for hooks in the airless framework.
    """

    def __init__(self):
        """Initializes a new instance of the FileHook class."""
        super().__init__()

    def write(self, local_filepath: str, data: Any, **kwargs) -> None:
        """
        Writes data to a local file with support for JSON and NDJSON formats.

        Args:
            local_filepath (str):
                The path to the local file where the data will be written.
            data (Any):
                The data to write to the file. It can be a string, dictionary, list,
                or any other type that can be serialized to JSON or converted to a string.
        Kwargs:
            use_ndjson (bool):
                If `True` and the data is a dictionary or list, the data will be
                written in NDJSON format. Defaults to `False`.
            mode (str):
                The mode in which the file is opened. Common modes include:
                - `'w'`: Write mode, which overwrites the file if it exists.
                - `'wb'`: Write binary mode, which overwrites the file if it exists.
                Defaults to `'w'`.
        """

        use_ndjson = kwargs.get('use_ndjson', False)
        mode = kwargs.get('mode', 'w')

        with open(local_filepath, mode) as f:
            if mode == 'wb':
                f.write(data)
            elif isinstance(data, (dict, list)):
                dump = ndjson.dump if use_ndjson else json.dump
                dump(data, f, default=str)
            else:
                f.write(str(data))

    def extract_filename(self, filepath_or_url: str) -> str:
        """Extracts the filename from a filepath or URL.

        Args:
            filepath_or_url (str): The original file path or URL.

        Returns:
            str: The extracted filename.
        """
        return filepath_or_url.split('/')[-1].split('?')[0].split('#')[0]

    def get_tmp_filepath(self, filepath_or_url: str, **kwargs) -> str:
        """
        Generates a temporary file path based on the provided filepath or URL.

        Args:
            filepath_or_url (str):
                The original file path or URL from which the filename is extracted.

        Kwargs:
            add_timestamp (bool, optional):
                If `True`, a timestamp and a UUID will be prefixed to the filename to ensure uniqueness.
                Defaults to `True`.

        Returns:
            str: The temporary file path.
        """
        add_timestamp = kwargs.get('add_timestamp', True)

        filename = self.extract_filename(filepath_or_url)
        if add_timestamp:
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            filename = f'{timestamp}_{uuid.uuid4().hex}_{filename}'
        return f'/tmp/{filename}'

    def download(
        self,
        url: str,
        headers: dict,
        timeout: int = 500,
        proxies: Optional[dict] = None,
        override_filename: Optional[str] = None,
    ) -> str:
        """Downloads a file from a given URL and saves it to a temporary path.

        Args:
            url (str): The URL of the file to download.
            headers (dict): The headers to include in the request.
            timeout (int, optional): The request timeout in seconds. Defaults to 500.
            proxies (dict, optional): Proxy settings for the request. Defaults to None.
            override_filename (str, optional): Used filename to override the original downloaded file name

        Returns:
            str: The local filename where the downloaded file is saved.
        """

        with requests.get(
            url,
            stream=True,
            verify=False,
            headers=headers,
            timeout=timeout,
            proxies=proxies,
        ) as r:
            r.raise_for_status()

            filename = None
            if 'Content-Disposition' in r.headers:
                matches = re.search(
                    r'filename="?([^";]+)"?', r.headers['Content-Disposition']
                )
                if matches:
                    filename = matches.group(1)

            local_filename = self.get_tmp_filepath(
                override_filename or filename or r.url
            )

            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return local_filename

    def rename(self, from_filename: str, to_filename: str) -> str:
        """Renames a file from the original filename to the new filename.

        Args:
            from_filename (str): The original filename to rename.
            to_filename (str): The new filename.

        Returns:
            str: The new filename after renaming.
        """

        to_filename_formatted = (
            '' if to_filename.startswith('/tmp/') else '/tmp/'
        ) + to_filename
        os.rename(from_filename, to_filename_formatted)
        return to_filename_formatted

    def rename_files(self, dir, prefix):
        """Renames all files in a directory by prepending a prefix.

        Args:
            dir (str): The directory containing files to rename.
            prefix (str): The prefix to prepend to each file name.
        """

        for root, subdirs, files in os.walk(dir):
            for filename in files:
                os.rename(
                    os.path.join(root, filename),
                    os.path.join(root, f'{prefix}_{filename}'),
                )

    def list_files(self, folder: str) -> list:
        """Lists all files in a specified directory.

        Args:
            folder (str): The folder path to search for files.

        Returns:
            list: A list of file paths found in the directory.
        """

        file_list = []
        for root, subdirs, files in os.walk(folder):
            for filename in files:
                filepath = os.path.join(root, filename)
                file_list.append(filepath)

        return file_list


class FtpHook(FileHook):
    """FtpHook class for handling FTP file operations.

    This class extends FileHook with methods specific to FTP file operations including
    connecting to an FTP server, navigating directories, and downloading files.
    """

    def __init__(self):
        """Initializes a new instance of the FtpHook class."""
        super().__init__()
        self.ftp = None

    def login(self, host, user, password):
        """Logs into the FTP server using the provided credentials.

        Args:
            host (str): The FTP server hostname or IP address.
            user (str): The username for the FTP server.
            password (str): The password for the FTP server.
        """

        self.ftp = FTP(host, user, password)
        self.ftp.login()

    def cwd(self, dir):
        """Changes the current working directory on the FTP server.

        Args:
            dir (str): The directory to change to.
        """

        if dir:
            self.ftp.cwd(dir)

    def dir(self) -> list:
        """Lists the files and directories in the current directory of the FTP server.

        This method retrieves a list of files and directories from the FTP server's
        current working directory. It populates a list with the directory entries
        and returns it.

        Returns:
            list: A list of directory entries as strings, each representing a file
            or directory in the FTP server's current working directory.
        """
        lines = []
        self.ftp.dir('', lines.append)
        return lines

    def list(self, regex: str = None, updated_after=None, updated_before=None) -> tuple:
        """Lists files in the current directory of the FTP server with optional filters.

        Args:
            regex (str, optional): A regular expression to filter file names. Defaults to None.
            updated_after (datetime, optional): Filter files updated after this date. Defaults to None.
            updated_before (datetime, optional): Filter files updated before this date. Defaults to None.

        Returns:
            tuple: A tuple containing two lists:
                - A list of files (dictionaries with 'name' and 'updated_at').
                - A list of directories (dictionaries with 'name' and 'updated_at').
        """

        lines = self.dir()

        files = []
        directories = []

        for line in lines:
            tokens = line.split()
            obj = {'name': tokens[3], 'updated_at': parser.parse(' '.join(tokens[:1]))}

            if regex and not re.search(regex, obj['name'], re.IGNORECASE):
                continue

            if updated_after and not (obj['updated_at'] >= updated_after):
                continue

            if updated_before and not (obj['updated_at'] <= updated_before):
                continue

            if tokens[2] == '<DIR>':
                directories.append(obj)
            else:
                files.append(obj)

        return files, directories

    def download(self, dir: str, filename: str) -> str:
        """Downloads a file from the FTP server to a temporary local file.

        Args:
            dir (str): The directory on the FTP server where the file is located.
            filename (str): The name of the file to download.

        Returns:
            str: The local filepath where the downloaded file is saved.
        """

        self.cwd(dir)
        local_filepath = self.get_tmp_filepath(filename)
        with open(local_filepath, 'wb') as file:
            self.ftp.retrbinary(f'RETR {filename}', file.write)
        return local_filepath
