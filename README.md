Python wrapper to support asynchronous `acli` commands.

## Install

Install the [Acquia CLI](https://docs.acquia.com/acquia-cloud-platform/add-ons/acquia-cli/acquia-cli-installation).

```
pip install git+https://github.com/NCIOCPL/pyacli.git
```

At this point you can `from pyacli import site_factory` or the other modules in it.

## Local Development 

For local development you can do an editable install:

```
pip install  -e .
```

## Use

## Site Factory

### Authentication

To authenticate you create a new instance of the `SiteFactory` class and pass in:

- Site Factory URI
- Username
- Key

You can have multiple Site Factory instances active at once and `pyacli` will ensure each one has the correct authentication before making calls.

```python
from site_factory import SiteFactory

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
```

#### Run

`run` is the workhorse method of `SiteFactory` and is designed to execute an `acli acsf:*` command for you. 

Parameters:

- `**args`: One or more ACSF commands with arguments as a tuple (e.g. `["acsf:sites:clear-cache", "1"]`)
- `**kwargs` of options:
  - `verbose`: Whether or not to print out information as it executes
  - `wait`: If `True` retrieves the task ID of the generated ACSF task and polls its status until completed
  - `interval`: If waiting, the interval to poll on
  - `max_checks`: If waiting, the max number of attempts at polling the status

```python

# Run commands against multiple factories
dev_acli.run(
    ["acsf:sites:find"],
    wait=False,
    verbose=False
    )

test_acli.run(
    ["acsf:sites:find"], 
    wait=False, 
    verbose=False
    )

# Run one or more commands and wait for the tasks they create to complete
dev_acli.run(
    ["acsf:sites:clear-cache", "123"], 
    ["acsf:sites:clear-cache", "456"],
    interval=5, max_checks=10
    )
```

#### Get Sites

`get_sites()` is a shortcut method that will execute `acli acsf:sites:find` and return just the site names and IDs. If you pass it any site names as strings then it will filter the list for you.

```python
# Get a list of all sites with IDs
print(dev_acli.get_sites())

# Filter to specific sites
print(dev_acli.get_sites("mysite1", "mysite2"))
```