"""
Cloud API module
"""

from pyacli.base_client import BaseAcliClient


class CloudAPI(BaseAcliClient):
    """
    Cloud API client.
    """

    def __init__(self, **auth_params):
        """
        Create an instance of a Cloud API login.

        :param auth_params: Authentication parameters required for the client.
        :type auth_params: dict

        :Keyword Arguments:
            - ACLI_KEY (str): An Acquia key for the user
            - ACLI_SECRET (str): The corresponding secret for the key
        """
        # pylint: disable=W0246 #useless super() delegation because we want to update the docstring above
        super().__init__(**auth_params)
        # pylint: enable=W0246

    def run(self, *commands: tuple, **options):
        """
        Runs a Cloud API acli command, optionally waiting for the command to finish executing.

        :param commands: Variable positional arguments representing ACLI commands and arguments as tuples.
        :type commands: tuple

        :param options: Additional keyword arguments for controlling execution options.
        :type options: dict

        :Keyword Arguments:
            - verbose (bool): Enable or disable verbose mode. Default is True.
            - wait (bool): Whether to wait for the completion of all tasks. Default is True.
            - max_retries (int): Maximum number of retries if task fails

        :return: List of decoded JSON objects representing the result of each ACLI command.
        :rtype: list
        """
        # pylint: disable=W0246 #useless super() delegation because we want to update the docstring above
        return super().run(*commands, **options)
        # pylint: enable=W0246

    def _extract_task_id(self, result):
        notification_href = result["_links"]["notification"]["href"]
        task_id = notification_href.split("/")[-1]
        return [task_id]

    def _validate_auth(self):
        self.run(["api:accounts:find"], verbose=False, wait=False)

    def _validate_commands(self, commands):
        # Ensure we're only executing ACE commands, because ACSF commands can't use app:task-wait
        if any(command[0].startswith("acsf:") for command in commands):
            raise ValueError(
                "This class should only be used with non-ACSF commands for acli"
            )

    def wait(self, task_id, **options):
        self.run(["app:task-wait", task_id], verbose=False, wait=False)

    def get_application(self, application_name: str):
        """
        Returns application ID for the provided application name.

        :param application_name: The machine name for the application contained in the hosting.id key
        :type application_name: string

        :return: An application ID
        :rtype: string
        """
        apps = self.run(["api:applications:list"], verbose=False, wait=False)[0]
        app = next(
            (
                app
                for app in apps
                if app.get("hosting", {}).get("id") == application_name
            ),
            None,
        )
        return app["uuid"]

    def get_environment(self, app_id: str, environment_name: str):
        """
        Returns environment ID for the provided environment name (ODE label).

        :param app_id: The ACE application to search for the environment within
        :type app_id: string

        :param environment_name: The environment (ODE) label to return
        :type environment_name: string

        :return: An environment ID
        :rtype: string
        """
        environments = self.run(
            ["api:applications:environment-list", app_id], verbose=False, wait=False
        )[0]
        env = next(
            (env for env in environments if env.get("label") == environment_name), None
        )

        return env

    def get_servers(self, app_id: str, environment_name: str, role: str = None):
        """
        Returns a list of servers, optionally filtered by server role.

        :param app_id: The ACE application to search for the environment within
        :type app_id: string

        :param environment_name: The environment (ODE) label to return
        :type environment_name: string

        :param role: The role of the servers to filter by
        :type role: string

        :return: A list of servers
        :rtype: dict
        """
        environment = self.get_environment(app_id, environment_name)
        servers = self.run(
            ["api:environments:servers-list", environment["id"]],
            wait=False,
            verbose=False,
        )[0]

        if role is not None:
            filtered_servers = [server for server in servers if role in server["roles"]]
        else:
            filtered_servers = servers

        return filtered_servers
