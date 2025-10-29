"""
Test pyacli.cloud_api server methods
"""

import os
from unittest.mock import patch
from .test_cloud_api_base import CloudAPITestBase


class TestCloudAPIServers(CloudAPITestBase):
    """
    Test Cloud API server-related methods
    """

    @patch("subprocess.Popen")
    def test_get_servers_success(self, mock_popen):
        """
        Test for success trying to get a list of servers
        """
        with open(
            os.path.join(
                self.cwd, "mocks/cloud_api/api_applications_environment-list.json"
            ),
            "rb",
        ) as f:
            file = f.read()
            mock_process_environments = self.create_mock_process(0, file)
        with open(
            os.path.join(
                self.cwd, "mocks/cloud_api/api_environments_servers-list.json"
            ),
            "rb",
        ) as f:
            file = f.read()
            mock_process_servers = self.create_mock_process(0, file)

        mock_popen.side_effect = [mock_process_environments, mock_process_servers]

        servers = self.cloud_api.get_servers("123", "Dev")
        self.assertEqual(servers[2]["id"], "1236")
        self.assertEqual(len(servers), 3)

    @patch("subprocess.Popen")
    def test_get_servers_success_filtered(self, mock_popen):
        """
        Test for success trying to filter a list of servers
        """
        with open(
            os.path.join(
                self.cwd, "mocks/cloud_api/api_applications_environment-list.json"
            ),
            "rb",
        ) as f:
            file = f.read()
            mock_process_environments = self.create_mock_process(0, file)
        with open(
            os.path.join(
                self.cwd, "mocks/cloud_api/api_environments_servers-list.json"
            ),
            "rb",
        ) as f:
            file = f.read()
            mock_process_servers = self.create_mock_process(0, file)

        mock_popen.side_effect = [mock_process_environments, mock_process_servers]

        servers = self.cloud_api.get_servers("123", "Dev", "web")
        self.assertEqual(servers[0]["id"], "1234")
        self.assertEqual(len(servers), 1)
