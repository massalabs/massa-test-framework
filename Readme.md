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

- Create a virtualenv:
    `python3 -m venv venv_dev`

- Install dev requirements:
    `venv_dev/bin/python -m pip install -r requirements-dev.txt`

## Tools

- Formatter [black](https://github.com/psf/black):
    `venv_dev/bin/black massa_test_framework`

- Typing [mypy](https://www.mypy-lang.org/): 
    `venv_dev/bin/mypy massa_test_framework`

- Linter [ruff](https://github.com/astral-sh/ruff):
    `venv_dev/bin/ruff check massa_test_framework`

- Doc [Sphinx](https://www.sphinx-doc.org):
    `cd doc && make html`

**Note:**

- Use Napoleon syntax when writing docstrings: [Napoleon Documentation](https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html)
  - For a full syntax example, refer to the [Example Google Docstring](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html#example-google).


## Generating massa_grpc

* python3 -m venv venv_grpc
* venv_grpc/bin/python -m pip install --upgrade betterproto[compiler]==2.0.0b5
* PATH=$PATH:venv_grpc/bin/ protoc -I$HOME/dev/massa-proto/proto/commons/ -I$HOME/dev/massa-proto/proto/apis/massa/api/v1/ -I$HOME/dev/massa-proto/proto/third_party/ --python_betterproto_out=massa $HOME/dev/massa-proto/proto/apis/massa/api/v1/api.proto