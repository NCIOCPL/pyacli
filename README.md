Python wrapper to support asynchronous `acli` commands.

## Install

Install the [Acquia CLI](https://docs.acquia.com/acquia-cloud-platform/add-ons/acquia-cli/acquia-cli-installation).

```
pip install git+https://github.com/NCIOCPL/pyacli.git
```

At this point you can `from pyacli import cloud_api`.

## Local Development 

For local development you can do an editable install:

```
pip install  -e .
```

## Use

### Cloud API

#### Authentication

To authenticate, create a new instance of the `CloudAPI` class and pass in:

- ACLI key
- ACLI secret

`pyacli` passes these values to `acli` through the environment before making calls.

```python
import os
from pyacli import cloud_api

auth = {
    "ACLI_KEY": os.environ["ACLI_KEY"],
    "ACLI_SECRET": os.environ["ACLI_SECRET"],
}
acli = cloud_api.CloudAPI(**auth)
```

#### Run

`run` executes one or more `acli` commands. If `wait` is enabled, it extracts the notification task from the command output and waits for completion with `app:task-wait`.

Parameters:

- `*commands`: One or more commands with arguments as a tuple (for example, `["api:environments:clear-caches", "environment-id"]`)
- `**kwargs` of options:
  - `verbose`: Whether or not to print out information as it executes
  - `wait`: If `True`, wait for generated tasks to complete
  - `max_retries`: Number of times to retry failed commands or tasks

```python
# Run a command and return immediately.
applications = acli.run(["api:applications:list"], wait=False, verbose=False)

# Run one or more commands and wait for the tasks they create to complete
acli.run(
    ["api:environments:clear-caches", "environment-id"],
    max_retries=2,
)
```

#### Helpers

The Cloud API client includes helpers for common lookups:

- `get_application(application_name)`
- `get_codebase(codebase_name)`
- `get_environment(container_id, environment_name, meo=False)`
- `get_servers(app_id, environment_name, role=None)`
- `get_meo_sites(codebase_id, *site_names)`
- `get_meo_sites_installed(codebase_id, environment_name, *site_names)`
