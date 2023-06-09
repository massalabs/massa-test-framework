# Massa test framework

A framework for Massa core dev to develop functional tests

# Quick start

```python
from pathlib import Path
from massa_test_framework import ServerOpts, Server, Node

# init a Server (using your computer)
server_opts = ServerOpts(local=True)
server = Server(server_opts) 
# create a Node object, use compilation from given path (assuming here it's compiled here in Sandbox mode)
node1 = Node.from_dev(server, repo=Path("~/dev/massa").expanduser())
# setup config
with node1.edit_config() as cfg:
    cfg["logging"]["level"] = 3

# start node
with node1.start():
    # Wait for node to be ready - aka node returns a valid last period
    node1.wait_ready(20)
    
    # Call get_status
    status = node1.get_status()
    print(status)
```

# Documentation



# Contrib rules

## Setup

    python3 -m venv venv_dev

## Tools

Formatter: [black](https://github.com/psf/black)
     
     venv_dev/bin/black massa_test_framework

Typing: [mypy](https://www.mypy-lang.org/)
     
     venv_dev/bin/mypy massa_test_framework

Linter: [ruff](https://github.com/astral-sh/ruff)

     venv_dev/bin/ruff check massa_test_framework

