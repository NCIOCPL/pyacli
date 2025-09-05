"""
ACSF Site Factory module
"""

import time
from pyacli.base_client import BaseAcliClient


class SiteFactory(BaseAcliClient):
    """
    ACSF API client.
    """

    def __init__(self, **auth_params):
        """
        Create an instance of an Acquia Site Factory client and then authenticate to it.

        :param auth_params: Authentication parameters required for the client.
        :type auth_params: dict

        :Keyword Arguments:
            - ACSF_FACTORY_URI (str): The URL to the Site Factory instance
            - ACSF_USERNAME (str): ACSF username
            - ACSF_KEY (str): ACSF key corresponding to the username
        """
        # pylint: disable=W0246 #useless super() delegation because we want to update the docstring above
        super().__init__(**auth_params)
        # pylint: enable=W0246

    def run(self, *commands: tuple, **options):
        """
        Runs an ACSF acli command, optionally waiting for the command to finish executing.

        :param commands: Variable positional arguments representing ACSF commands and arguments as tuples.
        :type commands: tuple

        :param options: Additional keyword arguments for controlling execution options.
        :type options: dict

        :Keyword Arguments:
            - verbose (bool): Enable or disable verbose mode. Default is True.
            - wait (bool): Whether to wait for the completion of all tasks. Default is True.
            - interval (int): Time interval (in seconds) for polling task completion status. Default is 60.
            - max_checks (int): Maximum number of attempts for polling task completion. Default is 120.
            - max_retries (int): Maximum number of retries if task fails

        :return: List of decoded JSON objects representing the result of each ACSF command.
        :rtype: list
        """
        # pylint: disable=W0246 #useless super() delegation because we want to update the docstring above
        return super().run(*commands, **options)
        # pylint: enable=W0246

    def _extract_task_id(self, result):
        task_ids = []
        if "task_ids" in result:
            task_ids = set(result["task_ids"].values())
        elif "task_id" in result:
            task_ids.append(result["task_id"])
        else:
            raise ValueError("Could not find any task IDs.")
        return task_ids

    def _validate_auth(self):
        self.run(["acsf:service-status:get"], verbose=False, wait=False)

    def _validate_commands(self, commands):
        # Ensure we're only executing ACSF commands, because task IDs are dependent
        if any(not command[0].startswith(("acsf:", "remote:")) for command in commands):
            raise ValueError(
                "This class should only be used with ACSF commands for acli"
            )

    def wait(self, task_id: int, **options):
        """
        Wait for a task to complete.

        No return. The method should finish executing once the task has completed.

        :param task_id: The Site Factory task to poll for updates.
        :type task_id: str

        :Keyword Arguments: Options inherited from the run class, to pass back to the run class. The following are used.
            - verbose (bool): Enable or disable verbose mode. Default is True.
            - interval (int): Time interval (in seconds) for polling task completion status. Default is 60.
            - max_checks (int): Maximum number of attempts for polling task completion. Default is 120.
        """
        verbose = options.get("verbose", False)
        interval = options.get("interval", 60)
        max_checks = options.get("max_checks", 120)

        attempt = 0
        while attempt < max_checks:
            if attempt != 0:
                time.sleep(interval)
            output = self.run(
                ["acsf:tasks:status", f"{task_id}"], verbose=False, wait=False
            )[0]
            wip_task = output["wip_task"]
            status = wip_task["status_string"]
            completed = int(wip_task["completed"])

            if completed > 0:
                if status == "Completed":
                    if verbose:
                        print(f"Task {task_id} completed.")
                    return output

                raise RuntimeError(
                    f"Task {task_id} completed but ended in status {status}"
                )

            if verbose:
                print(
                    f"Task {task_id} is still in status '{status}'. Waiting another {interval} seconds; status check {attempt+1}/{max_checks}."
                )
            attempt += 1
        raise RuntimeError(f"Command did not complete after {max_checks} status checks")

    def get_sites(self, *site_names: str):
        """
        Returns site IDs for the provided site names. Omitting site_names returns all sites.

        :param site_names: Variable positional arguments representing ACSF site names as strings.
        :type site_names: string

        :return: A list of site names and their corresponding IDs.
        :rtype: dict
        """
        # Going with a 1000 site limit and not worrying about paging
        output = self.run(
            ["acsf:sites:find", "--limit", "1000"], verbose=False, wait=False
        )[0]

        sites = {site.get("site"): site.get("id") for site in output.get("sites", [])}
        if site_names:
            sites = {
                site_name: site_id
                for site_name, site_id in sites.items()
                if site_name in site_names
            }

            missing_sites = [name for name in site_names if name not in sites]
            if missing_sites:
                raise ValueError(f"Site(s) not found: {', '.join(missing_sites)}")

        return sites
