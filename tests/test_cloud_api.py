"""
Test pyacli.cloud_api
"""

# pylint: disable=W0221 # override parent method arguments because setUp() has a patch
# pylint: disable=R0801 # testing code just looks very similar
# pylint: disable=W0212 # we're testing to make sure the protected members are set

import json
import os
import unittest
from unittest.mock import MagicMock, patch
from pyacli import cloud_api


class TestCloudAPI(unittest.TestCase):
    """
    Test Cloud API unit tests
    """

    @patch("subprocess.Popen")
    @patch("shutil.which")
    def setUp(self, mock_which, mock_popen):
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

    #########################################
    # __init__ method
    #########################################

    def test_init_success(self):
        """
        Test that the API instance has the correct authentication
        """

        self.assertEqual(self.cloud_api._acli_env["ACLI_KEY"], self.auth["ACLI_KEY"])
        self.assertEqual(
            self.cloud_api._acli_env["ACLI_SECRET"], self.auth["ACLI_SECRET"]
        )

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

    #########################################
    # run method
    #########################################

    @patch("subprocess.Popen")
    def test_run_wait_success(self, mock_popen):
        """
        Test the standard path of executing a command and polling tasks until completion.
        """

        with open(
            os.path.join(
                self.cwd, "mocks/cloud_api/api_environments_clear-caches.json"
            ),
            "rb",
        ) as f:
            file = f.read()
            mock_process_cache_clear = self.create_mock_process(0, file)
            expected_result = [json.loads(file)]
        with open(
            os.path.join(self.cwd, "mocks/cloud_api/api_app_task-wait.txt"), "rb"
        ) as f:
            mock_process_task_status_completed = self.create_mock_process(0, f.read())
        mock_popen.side_effect = [
            mock_process_cache_clear,
            mock_process_task_status_completed,
        ]

        result = self.cloud_api.run(
            ["api:environments:clear-caches", "123"], verbose=True, wait=True
        )
        self.assertEqual(result, expected_result)

    @patch("subprocess.Popen")
    def test_run_wait_retries_success(self, mock_popen):
        """
        Test handling retries when a wait fails.
        """

        with open(
            os.path.join(
                self.cwd, "mocks/cloud_api/api_environments_clear-caches.json"
            ),
            "rb",
        ) as f:
            file = f.read()
            mock_process_cache_clear = self.create_mock_process(0, file)
            expected_result = [json.loads(file)]
        mock_process_task_status_errored = self.create_mock_process(
            1, b"", b"Some error"
        )
        with open(
            os.path.join(self.cwd, "mocks/cloud_api/api_app_task-wait.txt"), "rb"
        ) as f:
            mock_process_task_status_completed = self.create_mock_process(0, f.read())
        mock_popen.side_effect = [
            mock_process_cache_clear,
            mock_process_task_status_errored,
            mock_process_cache_clear,
            mock_process_task_status_errored,
            mock_process_cache_clear,
            mock_process_task_status_completed,
        ]

        result = self.cloud_api.run(
            ["api:environments:clear-caches", "123"],
            verbose=True,
            wait=True,
            max_retries=2,
        )
        self.assertEqual(result, expected_result)

    @patch("subprocess.Popen")
    def test_run_wait_retries_failure(self, mock_popen):
        """
        Test running out of retries
        """

        with open(
            os.path.join(
                self.cwd, "mocks/cloud_api/api_environments_clear-caches.json"
            ),
            "rb",
        ) as f:
            file = f.read()
            mock_process_cache_clear = self.create_mock_process(0, file)
        mock_process_task_status_errored = self.create_mock_process(
            1, b"", b"Some error"
        )
        mock_popen.side_effect = [
            mock_process_cache_clear,
            mock_process_task_status_errored,
            mock_process_cache_clear,
            mock_process_task_status_errored,
        ]

        with self.assertRaises(RuntimeError) as e:
            self.cloud_api.run(
                ["api:environments:clear-caches", "123"],
                verbose=True,
                wait=True,
                max_retries=1,
            )

        self.assertEqual(str(e.exception), "No further retries specified, exiting.")

    @patch("subprocess.Popen")
    def test_run_no_wait_success(self, mock_popen):
        """
        Test executing a command and immediately completing without waiting for success.
        """

        with open(
            os.path.join(
                self.cwd, "mocks/cloud_api/api_environments_clear-caches.json"
            ),
            "rb",
        ) as f:
            file = f.read()
            mock_process = self.create_mock_process(0, file)
            expected_result = [json.loads(file)]

        mock_popen.return_value = mock_process

        result = self.cloud_api.run(
            ["api:environmentns:clear-caches", "123"], verbose=False, wait=False
        )
        self.assertEqual(result, expected_result)

    @patch("subprocess.Popen")
    def test_run_wait_failure(self, mock_popen):
        """
        Test executing a command that shouldn't be waited for.
        """

        with open(
            os.path.join(self.cwd, "mocks/cloud_api/api_applications_list.json"), "rb"
        ) as f:
            file = f.read()
            mock_process = self.create_mock_process(0, file)

        mock_popen.return_value = mock_process

        with self.assertRaises(ValueError) as e:
            self.cloud_api.run(["api:applications:list"], verbose=True, wait=True)

        self.assertTrue(
            str(e.exception).endswith("did not return any tasks to monitor.")
        )

    def test_run_acsf_failure(self):
        """
        Test for failure if we try to run an ACSF command
        """
        with self.assertRaises(ValueError) as e:
            self.cloud_api.run(
                ["acsf:sites:clear-cache", "441"], verbose=False, wait=False
            )

        self.assertEqual(
            str(e.exception),
            "This class should only be used with non-ACSF commands for acli",
        )

    @patch("subprocess.Popen")
    def test_run_command_failure(self, mock_popen):
        """
        Test for failure if the subprocess command just fails
        """
        command = "api:some:command"
        error = "Some error occurred but is not in stderr"
        mock_process = self.create_mock_process(
            1, bytes(f"{error}", encoding="utf-8"), b""
        )
        mock_popen.return_value = mock_process

        with self.assertRaises(RuntimeError) as e:
            self.cloud_api.run([command])
        print(e.exception)
        self.assertTrue(str(e.exception).startswith("Error running command"))
        self.assertTrue(str(e.exception).endswith(f"{command}': {error}"))

    #########################################
    # get_application method
    #########################################

    @patch("subprocess.Popen")
    def test_get_application_success(self, mock_popen):
        """
        Test for success trying to get all sites
        """

        with open(
            os.path.join(self.cwd, "mocks/cloud_api/api_applications_list.json"), "rb"
        ) as f:
            file = f.read()
            mock_process = self.create_mock_process(0, file)
        mock_popen.return_value = mock_process

        application_id = self.cloud_api.get_application("prod:myappcd")
        self.assertEqual(application_id, "bef1c24f-71d3-47ab-a226-5616b2ff2f5b")

    #########################################
    # get_environment method
    #########################################

    @patch("subprocess.Popen")
    def test_get_environment_success(self, mock_popen):
        """
        Test for success trying to get an environment
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

    #########################################
    # get_servers method
    #########################################

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


if __name__ == "__main__":
    unittest.main()
