"""
Test pyacli.cloud_api codebase methods
"""

import os
from unittest.mock import patch
from .test_cloud_api_base import CloudAPITestBase


class TestCloudAPICodebase(CloudAPITestBase):
    """
    Test Cloud API codebase-related methods
    """

    @patch("subprocess.Popen")
    def test_get_codebase_success(self, mock_popen):
        """
        Test for success trying to get a codebase (MEO)
        """
        with open(
            os.path.join(self.cwd, "mocks/cloud_api/api_codebases_get-all.json"), "rb"
        ) as f:
            file = f.read()
            mock_process = self.create_mock_process(0, file)
        mock_popen.return_value = mock_process

        application_id = self.cloud_api.get_codebase("examplemeo")
        self.assertEqual(application_id, "13d225e3-70cd-4430-9866-e08c8ae02662")

    @patch("subprocess.Popen")
    def test_get_codebase_failure(self, mock_popen):
        """
        Test for success trying to get a codebase (MEO)
        """
        with open(
            os.path.join(self.cwd, "mocks/cloud_api/api_codebases_get-all.json"), "rb"
        ) as f:
            file = f.read()
            mock_process = self.create_mock_process(0, file)
        mock_popen.return_value = mock_process

        with self.assertRaises(ValueError) as e:
            self.cloud_api.get_codebase("idontexist")
            self.assertEqual(e.exception, "No codebase found for that codebase name.")
