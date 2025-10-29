"""
Test pyacli.cloud_api application methods
"""

import os
from unittest.mock import patch
from .test_cloud_api_base import CloudAPITestBase


class TestCloudAPIApplication(CloudAPITestBase):
    """
    Test Cloud API application-related methods
    """

    @patch("subprocess.Popen")
    def test_get_application_success(self, mock_popen):
        """
        Test for success trying to get an application (non-MEO)
        """
        with open(
            os.path.join(self.cwd, "mocks/cloud_api/api_applications_list.json"), "rb"
        ) as f:
            file = f.read()
            mock_process = self.create_mock_process(0, file)
        mock_popen.return_value = mock_process

        application_id = self.cloud_api.get_application("prod:myappcd")
        self.assertEqual(application_id, "bef1c24f-71d3-47ab-a226-5616b2ff2f5b")
