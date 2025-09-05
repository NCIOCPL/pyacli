#!/usr/bin/env python

"""
Example script file showing basic pyacli usage.
"""

import os
from pyacli import site_factory

# Set up your site factories, passing in
#   - Site factory URI
#   - Username
#   - Key
dev_auth = {
    "ACSF_FACTORY_URI": os.environ["ACSF_DEV_FACTORY"],
    "ACSF_USERNAME": os.environ["ACSF_DEV_USERNAME"],
    "ACSF_KEY": os.environ["ACSF_DEV_KEY"],
}
dev_acli = site_factory.SiteFactory(**dev_auth)

test_auth = {
    "ACSF_FACTORY_URI": os.environ["ACSF_TEST_FACTORY"],
    "ACSF_USERNAME": os.environ["ACSF_TEST_USERNAME"],
    "ACSF_KEY": os.environ["ACSF_TEST_KEY"],
}
test_acli = site_factory.SiteFactory(**test_auth)

# Get a list of all sites with IDs
print(dev_acli.get_sites())
# Or filter to specific sites
print(dev_acli.get_sites("mysite1", "mysite2"))

# Run commands directly against multiple factories
print(dev_acli.run(["acsf:sites:find"], wait=False, verbose=False))
print(test_acli.run(["acsf:sites:find"], wait=False, verbose=False))

# Or run one or more commands and wait for the tasks they create to complete
print(
    dev_acli.run(
        ["acsf:sites:clear-cache", "123"],
        ["acsf:sites:clear-cache", "456"],
        interval=5,
        max_attempts=10,
    )
)
