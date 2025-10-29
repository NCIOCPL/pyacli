"""
Base test class for Cloud API tests
"""

import os
import unittest
from unittest.mock import MagicMock, patch
from pyacli import cloud_api


class CloudAPITestBase(unittest.TestCase):
    """
    Base class for Cloud API unit tests with shared setup and utilities
    """

    @patch("subprocess.Popen")
    @patch("shutil.which")
    # pylint: disable=W0221 # override parent method arguments because setUp() has a patch
    def setUp(self, mock_which, mock_popen):
        # pylint: enable=W0221
        """
        Set up the mock environment for all tests
        """

        # Patch shutil.which to always find acli
        mock_which.return_value = "/usr/local/bin/acli"

        # Set up authentication for all our tests
        self.cwd = os.path.dirname(os.path.realpath(__file__))
        with open(
            os.path.join(self.cwd, "mocks/cloud_api/api_accounts_find.json"), "rb"
        ) as f:
            mock_process = self.create_mock_process(0, f.read())
        mock_popen.return_value = mock_process

        self.auth = {
            "ACLI_KEY": "abcde12345",
            "ACLI_SECRET": "12345abcde",
        }
        self.cloud_api = cloud_api.CloudAPI(**self.auth)

    def create_mock_process(self, return_code, stdout_data=b"", stderr_data=b""):
        """
        Utility function for easily creating mock processes using MagicMock
        """
        mock_process = MagicMock()
        mock_process.__enter__.return_value.communicate.return_value = (
            stdout_data,
            stderr_data,
        )
        mock_process.__enter__.return_value.returncode = return_code

        return mock_process
