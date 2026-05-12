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
        # Retired acsf commands use a different task model and are no longer supported.
        if any(command[0].startswith("acsf:") for command in commands):
            raise ValueError("Retired acsf commands are no longer supported")

    def wait(self, task_id, **options):
        self.run(["app:task-wait", task_id], verbose=False, wait=False)

    #####
    # Below are helper functions to make interacting with Acquia easier.
    # Most commands can just be done via the end code but these are common enough
    # that it is helpful to make them generally available.
    #####

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

    def get_codebase(self, codebase_name: str):
        """
        Returns codebase ID for the provided codebase name.

        :param codebase_name: The machine name for the codebase
        :type codebase_name: string

        :return: A codebase ID
        :rtype: string
        """
        codebases = self.run(["api:codebases:get-all"], verbose=False, wait=False)[0]
        codebase = next(
            (
                codebase
                for codebase in codebases
                if codebase.get("label") == codebase_name
            ),
            None,
        )
        if codebase is None:
            raise ValueError("No codebase found for that codebase name.")
        return codebase["id"]

    def get_environment(
        self, container_id: str, environment_name: str, meo: bool = False
    ):
        """
        Returns environment ID for the provided environment name (ODE label).

        :param container_id: The ACE application or MEO codebase to search for the environment within
        :type container_id: string

        :param environment_name: The environment (ODE) label to return
        :type environment_name: string

        :param meo: Whether this search should be for a MEO codebase (true) or ACE application
        :type meo: bool

        :return: An environment object
        :rtype: dict
        """
        if not meo:
            environments = self.run(
                ["api:applications:environment-list", container_id],
                verbose=False,
                wait=False,
            )[0]
        else:
            environments = self.run(
                ["api:codebases:environments-list", container_id],
                verbose=False,
                wait=False,
            )[0]
        env = next(
            (env for env in environments if env.get("label") == environment_name), None
        )
        if env is None:
            raise ValueError("No environment found. Double check the provided name.")

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

    # Acquia MEO specific helper functions.

    def _filter_sites(self, sites_list: dict, site_names: tuple):
        """
        A helper to the helper because get_meo_sites and get_meo_sites_installed
        use nearly identical logic.

        :param sites_list: A JSON object returned by Acquia API with list of sites
        :type sites_list: dict

        :param site_names: Variable positional arguments representing MEO site names as strings.
        :type site_names: string

        :return: A list of site names and their corresponding IDs
        :rtype: dict
        """
        sites = {site.get("name"): site.get("id") for site in sites_list}
        if len(site_names) > 0:
            sites = {
                site_name: site_id
                for site_name, site_id in sites.items()
                if site_name in site_names
            }

            missing_sites = [name for name in site_names if name not in sites]
            if missing_sites:
                raise ValueError(f"Site(s) not found: {', '.join(missing_sites)}")

        return sites

    def get_meo_sites(self, codebase_id: str, *site_names: str):
        """
        Returns site IDs for the provided site names. Omitting site_names returns all sites.

        This returns the site IDs from the codebase itself, whether or not they have been installed
        on an environment in the codebase. This is needed in order to get the ID for a site
        _to install it_ on an environment.

        :param codebase_id: The codebase ID for the site instances
        :type codebase_id: string

        :param site_names: Variable positional arguments representing MEO site names as strings.
        :type site_names: string

        :return: A list of site names and their corresponding IDs
        :rtype: dict
        """
        # Hardcoding limit at 100 sites until that is a problem.
        sites_list = self.run(
            ["api:codebases:sites-list", "--limit", "100", codebase_id],
            wait=False,
            verbose=False,
        )[0]
        sites = self._filter_sites(sites_list, site_names)

        return sites

    def get_meo_sites_installed(
        self, codebase_id: str, environment_name: str, *site_names: str
    ):
        """
        Returns site IDs and environment ID for the provided site names. Omitting site_names returns all sites.

        This returns the site IDs for sites only if already installed to the given environment.

        :param codebase_id: The codebase ID for the site instances
        :type codebase_id: string

        :param environment_name: The environment (tier) the site instances are in
        :type environment_name: string

        :param site_names: Variable positional arguments representing MEO site names as strings.
        :type site_names: string

        :return: A list of site names and their corresponding IDs, and the environment ID
        :rtype: dict, str
        """
        environment = self.get_environment(codebase_id, environment_name, True)

        sites_list = self.run(
            ["api:environments:sites-list", environment["id"]],
            wait=False,
            verbose=False,
        )[0]
        sites = self._filter_sites(sites_list, site_names)

        # Because many site-instance commands also need the environment ID we return it here so
        # you can get away with only running a single command.
        return sites, environment["id"]
