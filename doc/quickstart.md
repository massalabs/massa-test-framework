# Quickstart

A quick way to use the framework

First step is to create a [Server](massa_test_framework.Server) object:

```
from massa_unit_test_framework import ServerOpts, Server
server_opts = ServerOpts(local=True)  # define a local server aka your computer
server = Server(server_opts)
```

Note: 
* You can also create a server object from ssh info, see [ServerOpts](massa_test_framework.ServerOpts)

This server will be used to define a [CompileUnit](massa_test_framework.CompileUnit) object that will clone then compile a Massa node:

```
from massa_unit_test_framework import CompileOpts, CompileUnit
compile_opts = CompileOpts()
compile_opts.clone_opts = [f"--branch testnet_24 --depth 1"]
compile_opts.build_opts = ["--features sandbox", "-j 12"]
cu = CompileUnit(server, compile_opts)
print("Compiling massa node...")
cu.compile()
print("Compilation Done.")
```

Note:
* You can apply patch before compilation, see [CompileUnit.add_patch](massa_test_framework.CompileUnit.add_patch)
* CompilationUnit can be created from an already compiled repository
* CompilationUnit can be shared between [Node](massa_test_framework.Node) object

From a server object and a compile unit object, a [Node](massa_test_framework.Node) object can be created:

```
node1 = Node.from_compile_unit(server, cu)
```

Note:
* When creating a node object, a tmp folder will be created and files from the compile unit will be copied there

Edit the config of this node (config.toml):

```
with node1.edit_config() as cfg:
    cfg["logging"]["level"] = 2
    cfg["bootstrap"]["bootstrap_list"] = []
```

Note:
* Several other config files can be edited in the same way

Once configured, you can then start the node and use the api like:

```
with node1.start():
    node1.wait_ready(timeout=20)
    print(node1.get_status())  # jsonrpc get status
    print(node1.get_version())  # grpc get version
```

That's all folks! And don't forget to view the [](api) page.

















