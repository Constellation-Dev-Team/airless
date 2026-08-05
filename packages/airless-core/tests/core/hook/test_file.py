# import os
import unittest

from unittest.mock import patch, MagicMock, mock_open

from airless.core.hook.file import FileHook, FtpHook


class TestFileHook(unittest.TestCase):
    def setUp(self):
        self.file_hook = FileHook()

    @patch('json.dump')
    @patch('builtins.open', new_callable=mock_open)
    def test_write_json(self, mock_file, mock_json_dump):
        data = {'key': 'value'}
        local_filepath = 'test.json'
        self.file_hook.write(local_filepath, data)

        mock_file.assert_called_once_with(local_filepath, 'w')
        mock_json_dump.assert_called_once_with(data, mock_file(), default=str)

    @patch('ndjson.dump')
    @patch('builtins.open', new_callable=mock_open)
    def test_write_ndjson(self, mock_file, mocK_ndjson_dump):
        data = [{'key': 'value1'}, {'key': 'value2'}]
        local_filepath = 'test.ndjson'
        self.file_hook.write(local_filepath, data, use_ndjson=True)

        mock_file.assert_called_once_with(local_filepath, 'w')
        mocK_ndjson_dump.assert_called_once_with(data, mock_file(), default=str)

    def test_extract_filename(self):
        url = 'http://example.com/path/to/file.txt?query=123'
        filename = self.file_hook.extract_filename(url)
        self.assertEqual(filename, 'file.txt')

    def test_get_tmp_filepath(self):
        filepath = '/path/to/file.txt'
        tmp_filepath = self.file_hook.get_tmp_filepath(filepath)
        self.assertTrue(tmp_filepath.startswith('/tmp/'))

    @patch('requests.get')
    def test_download(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_content.return_value = [b'data']
        mock_get.return_value = mock_response

        url = 'http://example.com/file.txt'
        headers = {'Authorization': 'Bearer token'}
        local_file = self.file_hook.download(url, headers)

        self.assertTrue(local_file.startswith('/tmp/'))
        mock_get.assert_called_once_with(
            url, stream=True, verify=False, headers=headers, timeout=500, proxies=None
        )

    @patch('os.remove')
    @patch('os.link')
    def test_rename(self, mock_link, mock_remove):
        from_filename = '/tmp/old_file.txt'
        to_filename = '/tmp/new_file.txt'
        result = self.file_hook.rename(from_filename, to_filename)
        mock_link.assert_called_once_with(from_filename, to_filename)
        mock_remove.assert_called_once_with(from_filename)
        self.assertEqual(result, to_filename)

    @patch('os.walk')
    @patch('os.rename')
    def test_rename_files(self, mock_rename, mock_walk):
        mock_walk.return_value = [
            ('/some/dir', ('subdir',), ('file1.txt', 'file2.txt')),
        ]
        self.file_hook.rename_files('/some/dir', 'prefix')
        mock_rename.assert_any_call('/some/dir/file1.txt', '/some/dir/prefix_file1.txt')
        mock_rename.assert_any_call('/some/dir/file2.txt', '/some/dir/prefix_file2.txt')

    @patch('os.walk')
    def test_list_files(self, mock_walk):
        mock_walk.return_value = [
            ('/some/dir', ('subdir',), ('file1.txt', 'file2.txt')),
        ]
        files = self.file_hook.list_files('/some/dir')
        self.assertEqual(files, ['/some/dir/file1.txt', '/some/dir/file2.txt'])


class TestFtpHook(unittest.TestCase):
    def setUp(self):
        self.ftp_hook = FtpHook()
        self.ftp_hook.ftp = MagicMock()

    @patch('airless.core.hook.file.FTP')
    def test_login(self, mock_ftp):
        host = 'ftp.example.com'
        user = 'username'
        password = 'password'

        self.ftp_hook.login(host, user, password)

        mock_ftp.assert_called_once_with(host, user, password)
        self.ftp_hook.ftp.login.assert_called_once()

    def test_cwd(self):
        directory = '/some/directory'
        self.ftp_hook.cwd(directory)
        self.ftp_hook.ftp.cwd.assert_called_once_with(directory)

    @patch.object(FtpHook, 'cwd')
    def test_list(self, mock_cwd):
        self.ftp_hook.dir = MagicMock(
            return_value=[
                '05-21-20  09:00AM        <DIR>   subdir1',
                '05-21-20  09:01AM                 1234 file1.txt',
                '05-21-20  09:02AM                 5678 file2.txt',
            ]
        )
        mock_cwd.return_value = None

        files, directories = self.ftp_hook.list()

        self.assertEqual(len(directories), 1)
        self.assertEqual(directories[0]['name'], 'subdir1')
        self.assertEqual(len(files), 2)
        self.assertEqual(files[0]['name'], 'file1.txt')
        self.assertEqual(files[1]['name'], 'file2.txt')

    @patch('airless.core.hook.file.FtpHook.cwd')
    @patch('builtins.open', new_callable=mock_open)
    def test_download(self, mock_file, mock_cwd):
        self.ftp_hook.cwd = MagicMock()
        filename = 'file.txt'
        directory = '/remote/dir'

        local_filepath = self.ftp_hook.download(directory, filename)

        self.assertTrue(local_filepath.startswith('/tmp/'))
        self.ftp_hook.cwd.assert_called_once_with(directory)
        self.ftp_hook.ftp.retrbinary.assert_called_once_with(
            f'RETR {filename}', mock_file().write
        )


if __name__ == '__main__':
    unittest.main()

