#!/usr/bin/env python

"""
Example script file showing basic pyacli Cloud API usage.
"""

import os
from pyacli import cloud_api

# Set up a Cloud API client, passing in an ACLI key and secret.
auth = {
    "ACLI_KEY": os.environ["ACLI_KEY"],
    "ACLI_SECRET": os.environ["ACLI_SECRET"],
}
acli = cloud_api.CloudAPI(**auth)

# Run commands directly.
print(acli.run(["api:applications:list"], wait=False, verbose=False))

application_name = os.environ.get("ACQUIA_APPLICATION_NAME")
environment_name = os.environ.get("ACQUIA_ENVIRONMENT_NAME")

application_id = acli.get_application(application_name)
environment = acli.get_environment(application_id, environment_name)

# Run a task-producing command and wait for it to complete.
print(
    acli.run(
        ["api:environments:clear-caches", environment["id"]],
        max_retries=2,
    )
)
