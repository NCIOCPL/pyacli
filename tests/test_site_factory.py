"""
Test pyacli.site_factory
"""

# pylint: disable=W0221 # override parent method arguments because setUp() has a patch
# pylint: disable=R0904 # too many public arguments: we have a lot of tests
# pylint: disable=R0801 # testing code just looks very similar
# pylint: disable=W0212 # we're testing to make sure the protected members are set

import json
import os
import unittest
from unittest.mock import MagicMock, patch
from pyacli import site_factory


class TestSiteFactory(unittest.TestCase):
    """
    Test Site Factory unit tests
    """

    @patch("subprocess.Popen")
    def setUp(self, mock_popen):
        """
        Set up ACSF authentication for all our tests
        """
        self.cwd = os.path.dirname(os.path.realpath(__file__))
        with open(
            os.path.join(self.cwd, "mocks/site_factory/acsf_service-status_get.json"),
            "rb",
        ) as f:
            mock_process = self.create_mock_process(0, f.read())
        mock_popen.return_value = mock_process

        self.auth = {
            "ACSF_FACTORY_URI": "https://www.example.com",
            "ACSF_USERNAME": "me@example.com",
            "ACSF_KEY": "abcde12345",
        }
        self.site_factory = site_factory.SiteFactory(**self.auth)

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
        Test that the site factory instance has the correct authentication
        """

        self.assertEqual(
            self.site_factory._acli_env["ACSF_FACTORY_URI"],
            self.auth["ACSF_FACTORY_URI"],
        )
        self.assertEqual(
            self.site_factory._acli_env["ACSF_USERNAME"], self.auth["ACSF_USERNAME"]
        )
        self.assertEqual(self.site_factory._acli_env["ACSF_KEY"], self.auth["ACSF_KEY"])

    def test_init_failure(self):
        """
        Test that calling a site factory with incorrect credentials causes failure.
        """
        bad_auth = {
            "ACSF_FACTORY_URI": "bad",
            "ACSF_USERNAME": "bad",
            "ACSF_KEY": "bad",
        }
        with self.assertRaises(RuntimeError) as e:
            site_factory.SiteFactory(**bad_auth)
        self.assertTrue(
            str(e.exception),
            "Authentication credentials do not seem to be valid. Please check them.",
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
            os.path.join(self.cwd, "mocks/site_factory/acsf_sites_clear-cache.json"),
            "rb",
        ) as f:
            file = f.read()
            mock_process_cache_clear = self.create_mock_process(0, file)
            expected_result = [json.loads(file)]
        with open(
            os.path.join(
                self.cwd, "mocks/site_factory/acsf_tasks_status_in-progress.json"
            ),
            "rb",
        ) as f:
            mock_process_task_status_in_progress = self.create_mock_process(0, f.read())
        with open(
            os.path.join(
                self.cwd, "mocks/site_factory/acsf_tasks_status_completed.json"
            ),
            "rb",
        ) as f:
            mock_process_task_status_completed = self.create_mock_process(0, f.read())
        mock_popen.side_effect = [
            mock_process_cache_clear,
            mock_process_task_status_in_progress,
            mock_process_task_status_completed,
        ]

        result = self.site_factory.run(
            ["acsf:sites:clear-cache", "441"],
            verbose=True,
            wait=True,
            interval=1,
            max_checks=10,
        )
        self.assertEqual(result, expected_result)

    @patch("subprocess.Popen")
    def test_run_wait_retries_success(self, mock_popen):
        """
        Test handling retries when a wait fails.
        """

        with open(
            os.path.join(self.cwd, "mocks/site_factory/acsf_sites_clear-cache.json"),
            "rb",
        ) as f:
            file = f.read()
            mock_process_cache_clear = self.create_mock_process(0, file)
            expected_result = [json.loads(file)]
        with open(
            os.path.join(
                self.cwd, "mocks/site_factory/acsf_tasks_status_in-progress.json"
            ),
            "rb",
        ) as f:
            mock_process_task_status_in_progress = self.create_mock_process(0, f.read())
        with open(
            os.path.join(self.cwd, "mocks/site_factory/acsf_tasks_status_errored.json"),
            "rb",
        ) as f:
            mock_process_task_status_errored = self.create_mock_process(0, f.read())
        with open(
            os.path.join(
                self.cwd, "mocks/site_factory/acsf_tasks_status_completed.json"
            ),
            "rb",
        ) as f:
            mock_process_task_status_completed = self.create_mock_process(0, f.read())
        mock_popen.side_effect = [
            mock_process_cache_clear,
            mock_process_task_status_in_progress,
            mock_process_task_status_errored,
            mock_process_cache_clear,
            mock_process_task_status_in_progress,
            mock_process_task_status_errored,
            mock_process_cache_clear,
            mock_process_task_status_in_progress,
            mock_process_task_status_completed,
        ]

        result = self.site_factory.run(
            ["acsf:sites:clear-cache", "441"],
            verbose=True,
            wait=True,
            interval=1,
            max_checks=10,
            max_retries=2,
        )
        self.assertEqual(result, expected_result)

    @patch("subprocess.Popen")
    def test_run_wait_single_id_success(self, mock_popen):
        """
        Test a command which returns only a single task ID instead of multiple.
        """

        with open(
            os.path.join(self.cwd, "mocks/site_factory/acsf_stage_start.json"), "rb"
        ) as f:
            file = f.read()
            mock_process_start = self.create_mock_process(0, file)
            expected_result = [json.loads(file)]
        with open(
            os.path.join(
                self.cwd, "mocks/site_factory/acsf_tasks_status_completed.json"
            ),
            "rb",
        ) as f:
            mock_process_task_status_completed = self.create_mock_process(0, f.read())
        mock_popen.side_effect = [
            mock_process_start,
            mock_process_task_status_completed,
        ]

        result = self.site_factory.run(["acsf:stage-v2:start"], verbose=True, wait=True)
        self.assertEqual(result, expected_result)

    @patch("subprocess.Popen")
    def test_run_no_wait_success(self, mock_popen):
        """
        Test executing a command and immediately completing without waiting for success.
        """

        with open(
            os.path.join(self.cwd, "mocks/site_factory/acsf_sites_clear-cache.json"),
            "rb",
        ) as f:
            file = f.read()
            mock_process = self.create_mock_process(0, file)
            expected_result = [json.loads(file)]

        mock_popen.return_value = mock_process

        result = self.site_factory.run(
            ["acsf:sites:clear-cache", "441"], verbose=False, wait=False
        )
        self.assertEqual(result, expected_result)

    @patch("subprocess.Popen")
    def test_run_empty_json_failure(self, mock_popen):
        """
        Test for fallback to text if an acli command returns an empty JSON object
        """
        mock_process = self.create_mock_process(0, b"")
        mock_popen.return_value = mock_process

        with self.assertRaises(RuntimeError) as e:
            self.site_factory.run(
                ["acsf:sites:clear-cache", "441"], verbose=False, wait=False
            )
        self.assertTrue(
            str(e.exception).startswith("Error decoding JSON from the output")
        )

    @patch("subprocess.Popen")
    def test_run_no_tasks_failure(self, mock_popen):
        """
        Test for failure if we're trying to wait but get back no task IDs
        """

        with open(
            os.path.join(self.cwd, "mocks/site_factory/acsf_sites_find.json"), "rb"
        ) as f:
            mock_process = self.create_mock_process(0, f.read())
        mock_popen.return_value = mock_process

        with self.assertRaises(ValueError) as e:
            self.site_factory.run(
                ["acsf:sites:clear-cache", "441"], verbose=False, wait=True
            )
        self.assertTrue(
            str(e.exception).endswith("did not return any tasks to monitor.")
        )

    @patch("subprocess.Popen")
    def test_run_wait_retries_falirue(self, mock_popen):
        """
        Test handling retries when a wait fails.
        """

        with open(
            os.path.join(self.cwd, "mocks/site_factory/acsf_sites_clear-cache.json"),
            "rb",
        ) as f:
            file = f.read()
            mock_process_cache_clear = self.create_mock_process(0, file)
        with open(
            os.path.join(
                self.cwd, "mocks/site_factory/acsf_tasks_status_in-progress.json"
            ),
            "rb",
        ) as f:
            mock_process_task_status_in_progress = self.create_mock_process(0, f.read())
        with open(
            os.path.join(self.cwd, "mocks/site_factory/acsf_tasks_status_errored.json"),
            "rb",
        ) as f:
            mock_process_task_status_errored = self.create_mock_process(0, f.read())
        mock_popen.side_effect = [
            mock_process_cache_clear,
            mock_process_task_status_in_progress,
            mock_process_task_status_errored,
            mock_process_cache_clear,
            mock_process_task_status_in_progress,
            mock_process_task_status_errored,
        ]

        with self.assertRaises(RuntimeError) as e:
            self.site_factory.run(
                ["acsf:sites:clear-cache", "441"],
                verbose=True,
                wait=True,
                interval=1,
                max_checks=10,
                max_retries=1,
            )
        self.assertEqual(str(e.exception), "No further retries specified, exiting.")

    @patch("subprocess.Popen")
    def test_run_sf_failure(self, mock_popen):
        """
        Test for failure if the site factory returns a valid json object
        """
        mock_process = self.create_mock_process(
            1, b'{"error": "Some error occurred"}', b""
        )
        mock_popen.return_value = mock_process

        with self.assertRaises(RuntimeError) as e:
            self.site_factory.run(["acsf:sites:find"])
        self.assertGreater(
            str(e.exception).find('{"error": "Some error occurred"}'), -1
        )

    @patch("subprocess.Popen")
    def test_run_command_failure(self, mock_popen):
        """
        Test for failure if the subprocess command just fails
        """
        mock_process = self.create_mock_process(1, b"", b"Some error occurred")
        mock_popen.return_value = mock_process

        with self.assertRaises(ValueError) as e:
            self.site_factory.run(["invalid_command"])
        self.assertEqual(
            str(e.exception),
            "This class should only be used with ACSF commands for acli",
        )

    #########################################
    # wait method
    #########################################

    @patch("subprocess.Popen")
    def test_wait_success(self, mock_popen):
        """
        Test a standard process where we wait for a task to complete
        """

        with open(
            os.path.join(
                self.cwd, "mocks/site_factory/acsf_tasks_status_in-progress.json"
            ),
            "rb",
        ) as f:
            mock_process_progress = self.create_mock_process(0, f.read())
        with open(
            os.path.join(
                self.cwd, "mocks/site_factory/acsf_tasks_status_completed.json"
            ),
            "rb",
        ) as f:
            file = f.read()
            mock_process_complete = self.create_mock_process(0, file)
            expected_result = json.loads(file)
        mock_popen.side_effect = [
            mock_process_progress,
            mock_process_progress,
            mock_process_complete,
        ]

        result = self.site_factory.wait(123, verbose=True, interval=1, max_checks=100)
        self.assertEqual(result, expected_result)

    @patch("subprocess.Popen")
    def test_wait_timeout_failure(self, mock_popen):
        """
        Test for failure if we don't receive success within our max_checks
        """

        with open(
            os.path.join(
                self.cwd, "mocks/site_factory/acsf_tasks_status_in-progress.json"
            ),
            "rb",
        ) as f:
            mock_process = self.create_mock_process(0, f.read())
        mock_popen.return_value = mock_process

        with self.assertRaises(RuntimeError) as e:
            self.site_factory.wait(123, verbose=True, interval=1, max_checks=2)
        self.assertEqual(
            str(e.exception), "Command did not complete after 2 status checks"
        )

    @patch("subprocess.Popen")
    def test_wait_task_failure(self, mock_popen):
        """
        Test for failure if the task fails
        """

        with open(
            os.path.join(self.cwd, "mocks/site_factory/acsf_tasks_status_errored.json"),
            "rb",
        ) as f:
            mock_process = self.create_mock_process(0, f.read())
        mock_popen.return_value = mock_process

        with self.assertRaises(RuntimeError) as e:
            self.site_factory.wait(456)
        self.assertEqual(
            str(e.exception), "Task 456 completed but ended in status Errored"
        )

    @patch("subprocess.Popen")
    def test_wait_command_failure(self, mock_popen):
        """
        Test for failure if the acli command happens to fail
        """
        mock_process = self.create_mock_process(1, b"", b"Some error occurred")
        mock_popen.return_value = mock_process

        with self.assertRaises(RuntimeError) as e:
            self.site_factory.wait(456)
        self.assertTrue(str(e.exception).startswith("Error running command"))

    #########################################
    # get_sites method
    #########################################

    @patch("subprocess.Popen")
    def test_get_sites_all_success(self, mock_popen):
        """
        Test for success trying to get all sites
        """

        with open(
            os.path.join(self.cwd, "mocks/site_factory/acsf_sites_find.json"), "rb"
        ) as f:
            file = f.read()
            mock_process = self.create_mock_process(0, file)
            mock_sites = json.loads(file)
        mock_popen.return_value = mock_process

        sites = self.site_factory.get_sites()
        self.assertEqual(len(sites), len(mock_sites["sites"]))

    @patch("subprocess.Popen")
    def test_get_sites_filter_success(self, mock_popen):
        """
        Test for success trying to get a filtered list of sites
        """

        with open(
            os.path.join(self.cwd, "mocks/site_factory/acsf_sites_find.json"), "rb"
        ) as f:
            mock_process = self.create_mock_process(0, f.read())
        mock_popen.return_value = mock_process

        sites = self.site_factory.get_sites("mysite1", "mysite2")
        self.assertEqual(sites, {"mysite1": 411, "mysite2": 426})

    @patch("subprocess.Popen")
    def test_get_sites_non_existent_failure(self, mock_popen):
        """
        Test for failure if I ask for a site that doesn't exist
        """

        with open(
            os.path.join(self.cwd, "mocks/site_factory/acsf_sites_find.json"), "rb"
        ) as f:
            mock_process = self.create_mock_process(0, f.read())
        mock_popen.return_value = mock_process

        with self.assertRaises(ValueError) as e:
            self.site_factory.get_sites("mysite1", "sitenoexist")
        self.assertEqual(str(e.exception), "Site(s) not found: sitenoexist")

    @patch("subprocess.Popen")
    def test_get_sites_command_failure(self, mock_popen):
        """
        Test for failure if the acli command fails out
        """

        mock_process = self.create_mock_process(1, b"", b"Some error occurred")
        mock_popen.side_effect = [mock_process]

        with self.assertRaises(RuntimeError) as e:
            self.site_factory.get_sites("site1", "site2")
        self.assertTrue(str(e.exception).startswith("Error running command"))


if __name__ == "__main__":
    unittest.main()
