"""
Test pyacli.cloud_api environment methods
"""

import os
from unittest.mock import patch
from .test_cloud_api_base import CloudAPITestBase


class TestCloudAPIEnvironment(CloudAPITestBase):
    """
    Test Cloud API environment-related methods
    """

    @patch("subprocess.Popen")
    def test_get_environment_success(self, mock_popen):
        """
        Test for success trying to get an environment non-MEO
        """
        with open(
            os.path.join(
                self.cwd, "mocks/cloud_api/api_applications_environment-list.json"
            ),
            "rb",
        ) as f:
            file = f.read()
            mock_process = self.create_mock_process(0, file)
        mock_popen.return_value = mock_process

        env = self.cloud_api.get_environment("123", "ACLI Creation")
        self.assertEqual(env["id"], "146146-f1dc8929-04ba-4fc8-875b-f19264dc568e")

    @patch("subprocess.Popen")
    def test_get_environment_success_codebase(self, mock_popen):
        """
        Test for success trying to get an environment MEO
        """
        with open(
            os.path.join(
                self.cwd, "mocks/cloud_api/api_codebases_environments-list.json"
            ),
            "rb",
        ) as f:
            file = f.read()
            mock_process = self.create_mock_process(0, file)
        mock_popen.return_value = mock_process

        env = self.cloud_api.get_environment("123", "Prod", True)
        self.assertEqual(env["id"], "b700df4a-ca0d-4372-9f5d-2960c5745930")

    @patch("subprocess.Popen")
    def test_get_environment_failure(self, mock_popen):
        """
        Test for failure when getting non-existent environment
        """
        with open(
            os.path.join(
                self.cwd, "mocks/cloud_api/api_codebases_environments-list.json"
            ),
            "rb",
        ) as f:
            file = f.read()
            mock_process = self.create_mock_process(0, file)
        mock_popen.return_value = mock_process

        with self.assertRaises(ValueError) as e:
            self.cloud_api.get_environment("123", "nonexistent")
        self.assertEqual(
            str(e.exception),
            "No environment found. Double check the provided name.",
        )

    @patch("subprocess.Popen")
    def test_get_environment_failure_codebase(self, mock_popen):
        """
        Test for failure when getting non-existent environment from MEO
        """
        with open(
            os.path.join(
                self.cwd, "mocks/cloud_api/api_codebases_environments-list.json"
            ),
            "rb",
        ) as f:
            file = f.read()
            mock_process = self.create_mock_process(0, file)
        mock_popen.return_value = mock_process

        with self.assertRaises(ValueError) as e:
            self.cloud_api.get_environment("123", "nonexistent", True)
        self.assertEqual(
            str(e.exception),
            "No environment found. Double check the provided name.",
        )
