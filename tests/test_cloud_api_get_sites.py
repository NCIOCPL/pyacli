"""
Test pyacli.cloud_api MEO site methods
"""

import os
from unittest.mock import patch
from .test_cloud_api_base import CloudAPITestBase


class TestCloudAPISites(CloudAPITestBase):
    """
    Test Cloud API site-related methods
    """

    @patch("subprocess.Popen")
    def test_get_sites_all_success(self, mock_popen):
        """
        Test for success trying to get a list of sites
        """
        with open(
            os.path.join(self.cwd, "mocks/cloud_api/api_codebases_sites-list.json"),
            "rb",
        ) as f:
            file = f.read()
            mock_process_sites = self.create_mock_process(0, file)

        mock_popen.return_value = mock_process_sites

        sites = self.cloud_api.get_meo_sites(
            "13d225e3-70cd-4430-9866-e08c8ae02662",
        )
        self.assertEqual(len(sites), 3)

    @patch("subprocess.Popen")
    def test_get_sites_one_success(self, mock_popen):
        """
        Test for success trying to get a single site
        """
        with open(
            os.path.join(self.cwd, "mocks/cloud_api/api_codebases_sites-list.json"),
            "rb",
        ) as f:
            file = f.read()
            mock_process_sites = self.create_mock_process(0, file)

        mock_popen.return_value = mock_process_sites

        sites = self.cloud_api.get_meo_sites(
            "13d225e3-70cd-4430-9866-e08c8ae02662", "site2"
        )
        self.assertEqual(len(sites), 1)
        self.assertEqual(sites.get("site2"), "1b70caa3-c4f9-40df-848f-e76d4c6a31d7")

    @patch("subprocess.Popen")
    def test_get_sites_failure(self, mock_popen):
        """
        Test for failure getting an unknown site
        """
        with open(
            os.path.join(self.cwd, "mocks/cloud_api/api_codebases_sites-list.json"),
            "rb",
        ) as f:
            file = f.read()
            mock_process_sites = self.create_mock_process(0, file)

        mock_popen.return_value = mock_process_sites

        with self.assertRaises(ValueError) as e:
            self.cloud_api.get_meo_sites(
                "13d225e3-70cd-4430-9866-e08c8ae02662", "badsite"
            )
            self.assertEqual(str(e.exception), "Site(s) not found: badsite")

    @patch("subprocess.Popen")
    def test_get_sites_installed_all_success(self, mock_popen):
        """
        Test for success trying to get a list of site instances for a MEO environment
        """
        with open(
            os.path.join(
                self.cwd, "mocks/cloud_api/api_codebases_environments-list.json"
            ),
            "rb",
        ) as f:
            file = f.read()
            mock_process_environments = self.create_mock_process(0, file)
        with open(
            os.path.join(self.cwd, "mocks/cloud_api/api_environments_sites-list.json"),
            "rb",
        ) as f:
            file = f.read()
            mock_process_sites = self.create_mock_process(0, file)

        mock_popen.side_effect = [
            mock_process_environments,
            mock_process_sites,
        ]

        sites_installed, environment = self.cloud_api.get_meo_sites_installed(
            "13d225e3-70cd-4430-9866-e08c8ae02662", "Prod"
        )
        self.assertEqual(len(sites_installed), 3)
        self.assertEqual(environment, "b700df4a-ca0d-4372-9f5d-2960c5745930")

    @patch("subprocess.Popen")
    def test_get_sites_installed_one_success(self, mock_popen):
        """
        Test for success trying to get a single site instance for a MEO environment
        """
        with open(
            os.path.join(
                self.cwd, "mocks/cloud_api/api_codebases_environments-list.json"
            ),
            "rb",
        ) as f:
            file = f.read()
            mock_process_environments = self.create_mock_process(0, file)
        with open(
            os.path.join(self.cwd, "mocks/cloud_api/api_environments_sites-list.json"),
            "rb",
        ) as f:
            file = f.read()
            mock_process_sites = self.create_mock_process(0, file)

        mock_popen.side_effect = [
            mock_process_environments,
            mock_process_sites,
        ]

        sites_installed, _ = self.cloud_api.get_meo_sites_installed(
            "13d225e3-70cd-4430-9866-e08c8ae02662", "Prod", "site2"
        )
        self.assertEqual(len(sites_installed), 1)
        self.assertEqual(
            sites_installed.get("site2"), "1b70caa3-c4f9-40df-848f-e76d4c6a31d7"
        )

    @patch("subprocess.Popen")
    def test_get_sites_installed_failure(self, mock_popen):
        """
        Test for failure trying to get an unknown site
        """
        with open(
            os.path.join(
                self.cwd, "mocks/cloud_api/api_codebases_environments-list.json"
            ),
            "rb",
        ) as f:
            file = f.read()
            mock_process_environments = self.create_mock_process(0, file)
        with open(
            os.path.join(self.cwd, "mocks/cloud_api/api_environments_sites-list.json"),
            "rb",
        ) as f:
            file = f.read()
            mock_process_sites = self.create_mock_process(0, file)

        mock_popen.side_effect = [
            mock_process_environments,
            mock_process_sites,
        ]
        with self.assertRaises(ValueError) as e:
            self.cloud_api.get_meo_sites_installed(
                "13d225e3-70cd-4430-9866-e08c8ae02662", "Prod", "badsite"
            )
            self.assertEqual(str(e.exception), "Site(s) not found: badsite")
