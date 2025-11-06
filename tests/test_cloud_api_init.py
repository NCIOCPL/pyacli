"""
Test pyacli.cloud_api initialization
"""

from unittest.mock import patch
from pyacli import cloud_api
from .test_cloud_api_base import CloudAPITestBase


class TestCloudAPIInit(CloudAPITestBase):
    """
    Test Cloud API initialization
    """

    def test_init_success(self):
        """
        Test that the API instance has the correct authentication
        """
        # pylint: disable=W0212 # we're testing to make sure the protected members are set
        self.assertEqual(self.cloud_api._acli_env["ACLI_KEY"], self.auth["ACLI_KEY"])
        self.assertEqual(
            self.cloud_api._acli_env["ACLI_SECRET"], self.auth["ACLI_SECRET"]
        )
        # pylint: enable=W0212

    @patch("shutil.which")
    def test_init_failure(self, mock_which):
        """
        Test that calling a API with incorrect credentials causes failure.
        """
        # This test creates a client instance separate from the one in setUp(),
        # so we need to patch which() again.
        mock_which.return_value = "/usr/local/bin/acli"
        bad_auth = {
            "ACLI_KEY": "bad",
            "ACLI_SECRET": "bad",
        }
        with self.assertRaises(RuntimeError) as e:
            cloud_api.CloudAPI(**bad_auth)
        self.assertEqual(
            str(e.exception),
            "Authentication credentials do not seem to be valid. Please check them.",
        )

    @patch("shutil.which")
    def test_init_without_acli(self, mock_which):
        """
        Test that calling an API without acli installed causes failure.
        """
        # setUp() makes it look like acli is installed, but for this test we want
        # it to not be installed.
        mock_which.return_value = None
        with self.assertRaises(RuntimeError) as e:
            cloud_api.CloudAPI(**self.auth)
        self.assertEqual(
            str(e.exception),
            "The 'acli' command was not found in your PATH. Please install the Acquia CLI and ensure it is available in your PATH.",
        )
