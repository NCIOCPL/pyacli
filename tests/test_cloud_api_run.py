"""
Test pyacli.cloud_api run method
"""

import json
import os
from unittest.mock import patch
from .test_cloud_api_base import CloudAPITestBase


class TestCloudAPIRun(CloudAPITestBase):
    """
    Test Cloud API run method
    """

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
