"""
Base acli module
"""

import json
import os
import shutil
import subprocess
from abc import ABC, abstractmethod


class BaseAcliClient(ABC):
    """
    Base class for cloud API clients.
    """

    def __init__(self, **auth_params):
        """
        Store the necessary authentication parameters and validate connection.

        :Keyword Arguments: A list of environment variables needed for authentication as key/value pairs. These will be passed to acli directly.
        """

        # Get the ACLI executable path
        self._acli_executable = shutil.which("acli")
        if self._acli_executable is None:
            raise RuntimeError(
                "The 'acli' command was not found in your PATH. Please install the Acquia CLI and ensure it is available in your PATH."
            )

        # Set the necessary ACLI environment variables for execution
        self._acli_env = os.environ.copy()
        for param, value in auth_params.items():
            self._acli_env[param] = value
        try:
            self._validate_auth()
        except Exception as e:
            raise RuntimeError(
                "Authentication credentials do not seem to be valid. Please check them."
            ) from e

    def run(self, *commands: tuple, **options):
        """
        Execute API commands, optionally waiting for completion of all tasks associated with them.

        :param commands: Variable positional arguments representing commands and arguments as tuples.
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
        verbose = options.get("verbose", True)
        wait_for_completion = options.get("wait", True)
        max_retries = options.get("max_retries", 2)

        self._validate_commands(commands)

        command_results = []
        task_ids = {}
        for command in commands:
            executable_command = [self._acli_executable, *command]
            str_command = " ".join(str(item) for item in executable_command)

            if verbose:
                print(f"Running ACLI command '{str_command}'")

            # Execute the actual acli commands using subprocess
            with subprocess.Popen(
                executable_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=self._acli_env,
            ) as process:
                output, error = process.communicate()
                return_code = process.returncode
                error = error.decode("utf-8")

            if return_code != 0:
                if error == "":
                    error = output.decode("utf-8")
                if max_retries > 0 and self._should_retry_command_error(error):
                    print(
                        f"ACLI app error detected, will retry ({max_retries - 1} retries remaining after this one)"
                    )
                    rerun_options = options.copy()
                    rerun_options["max_retries"] = max_retries - 1
                    command_results.extend(self.run(list(command), **rerun_options))
                    continue
                raise RuntimeError(f"Error running command '{str_command}': {error}")

            try:
                # Assume all ACLI output is JSON.
                result = json.loads(output)
            except json.JSONDecodeError as e:
                # At least the app:task-wait is not JSON so we can't throw an error
                result = output.decode("utf-8")
                # But we really only want the last few lines in that situation
                # Otherwise we get a bunch of "Waiting for task" lines dumped on us all at once
                result_lines = result.splitlines()[-7:]
                result = "\n".join(result_lines)
                # And if we end up with a blank result, raise the JSON error
                if result == "":
                    raise RuntimeError(
                        f"Error decoding JSON from the output: {e}, {error}"
                    ) from e
            command_results.append(result)

            # Extract the task_ids if we need to wait for completion
            if wait_for_completion:
                try:
                    extracted_ids = self._extract_task_id(result)
                except Exception as e:
                    raise ValueError(
                        "The command did not return any tasks to monitor."
                    ) from e
                for task_id in extracted_ids:
                    task_ids[task_id] = list(command)

            if verbose:
                print(json.dumps(result, indent=4))

        # Wait for completion if necessary
        retry_commands = []
        if wait_for_completion:
            for task_id, command in task_ids.items():
                try:
                    self.wait(task_id, **options)
                except RuntimeError as e:
                    if max_retries > 0:
                        print(str(e))
                        print(
                            f"Task failed, will retry ({max_retries - 1} retries remaining after this one)"
                        )
                        retry_commands.append(command)
                    else:
                        raise RuntimeError(
                            "No further retries specified, exiting."
                        ) from e

        # Re-run anything that fails if we have retries available
        if len(retry_commands) > 0:
            rerun_options = options
            rerun_options["max_retries"] = max_retries - 1

            self.run(
                *retry_commands,
                **rerun_options,
            )

        return command_results

    def _should_retry_command_error(self, error: str) -> bool:
        """
        Return whether an ACLI command error looks like a transient app failure.

        ACLI occasionally throws a syntax error when an upstream response is
        malformed. Those failures are unrelated to the requested command itself
        and are safe to retry.
        """
        normalized_error = error.lower()
        return "syntax error" in normalized_error

    @abstractmethod
    def _extract_task_id(self, result):
        """
        Extract the task ID to monitor for waiting.

        :param result: The acli output containing the task ID to extract.
        :type result: Varies

        :return: A task ID for
        :rtype: str
        """

    @abstractmethod
    def _validate_auth(self):
        """
        Validate authentication credentials.

        No return. The method should raise an error if the authentication credentials are invalid.
        """

    @abstractmethod
    def _validate_commands(self, commands):
        """
        Validate acli commands.

        No return. The method should raise an error if the commands are invalid.

        :param commands: A list containing acli commands to validate.
        :type commands: list
        """

    @abstractmethod
    def wait(self, task_id, **options):
        """
        Wait for a task to complete.

        No return. The method should finish executing once the task has completed.

        :param task_id: The Acquia task to poll for updates.
        :type task_id: str

        :Keyword Arguments: A list of options to pass to the wait method, defined by the derived class.
        """
