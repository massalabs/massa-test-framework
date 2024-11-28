import sys
import asyncio
from contextlib import contextmanager
from pathlib import Path
import json
import time
from urllib.parse import urlparse

from typing import Container, Generator, List, Dict, Optional, Callable, Union

import betterproto
from grpclib.client import Channel
from massa_proto_python.massa.model.v1 import ReadOnlyExecutionOutput

# internal
from massa_test_framework import massa_jsonrpc_api
from massa_proto_python.massa.api.v1 import (
    ExecuteReadOnlyCallRequest,
    ExecuteReadOnlyCallResponse,
    GetMipStatusRequest,
    GetMipStatusResponse,
    PublicServiceStub,
    PrivateServiceStub,
    GetStatusRequest,
    GetStatusResponse,
    GetStakersRequest,
    GetStakersResponse,
    QueryStateResponse,
    QueryStateRequest,
)


from massa_test_framework.massa_jsonrpc_api import AddressInfo, Api2
from massa_test_framework.compile import CompileUnit, CompileOpts
from massa_test_framework.remote import copy_file, RemotePath
from massa_test_framework.server import Server, MassaNodeOpts

# third party
import requests
import tomlkit
from tomlkit.toml_document import TOMLDocument



class Node:
    def __init__(self, server: Server, compile_unit: CompileUnit):
        """Init a Node (e.g. a Massa Node) object

        The new node can be started, stopped, edited (various config files)

        Args:
            server: the server on which the node will run on
            compile_unit: the compilation of the massa repo

        Raises:
            RuntimeError: if api ports && grpc port cannot be read from config

        """

        self.server = server
        self.compile_unit = compile_unit

        self._to_install: Dict[str, Path] = {
            "massa_node": self.compile_unit.massa_node,
            "massa_client": self.compile_unit.massa_client,
        }
        self._to_install.update(self.compile_unit.config_files)
        self._to_create = ["massa-node", "massa-node/config", "massa-client"]

        self.node_start_cmd = ["./massa-node", "-p", "1234"]
        self.node_stop_cmd = ""

        # setup node
        self.install_folder = self._install()
        self.config_files = {
            k: self.install_folder / p
            for k, p in self.compile_unit.config_files.items()
        }
        # print(self.config_files)


    def _install(self) -> Path | RemotePath:
        tmp_folder = self.server.mkdtemp(prefix="massa_")
        repo = self.compile_unit.repo

        for to_create in self._to_create:
            f = Path(tmp_folder) / to_create
            self.server.mkdir(Path(f))

        for filename, to_install in self._to_install.items():
            src = repo / to_install

            if filename == "massa_node":
                dst = tmp_folder / "massa-node" / to_install.name
            elif filename == "massa_client":
                dst = tmp_folder / "massa-client" / to_install.name
            elif filename == "node_privkey.key":
                continue
            else:
                dst = tmp_folder / to_install
            self.server.mkdir(dst.parent)
            copy_file(src, dst)

        return tmp_folder

    @staticmethod
    def from_compile_unit(server: Server, compile_unit: CompileUnit) -> "Node":
        node = Node(server, compile_unit)
        return node

    @staticmethod
    def from_dev(
        server: Server, repo: Path, build_opts: Optional[List[str]] = None
    ) -> "Node":
        # TODO: add options to recompile?
        compile_opts = CompileOpts()
        compile_opts.already_compiled = repo
        if build_opts:
            compile_opts.build_opts = build_opts
        cu = CompileUnit(server, compile_opts)
        node = Node(server, cu)
        return node

    # @contextmanager
    # def start0(self):
    #     process = self.server.run(
    #         [" ".join(self.node_start_cmd)], cwd=self.install_folder
    #     )
    #     print("[node start] process type:", type(process))
    #     try:
    #         print("[node start] yield", process)
    #         # Note: Subprocess.Popen execute as soon as it is instantiated and return an object
    #         #       while ParamikoRemotePopen.run return a context mngr (and it must be used, using 'with')
    #         if hasattr(process, "__enter__"):
    #             with process as p:
    #                 yield p
    #         else:
    #             yield process
    #     finally:
    #         print("[node start] will stop", process)
    #         self.stop(process)

    @contextmanager
    def start(
        self,
        env: Optional[Dict[str, str]] = None,
        args: Optional[List[str]] = None,
        stdout=sys.stdout,
        stderr=sys.stderr,
    ):
        """Start a node

        Start a Massa node (as a context manager)

        Args:
            env:
            args: additional node arguments (e.g. ["--restart-from-snapshot-at-period", "10"])
            stdout: where to log node standard output (default to sys.stdout)
            stderr: where to log node standard error output (default to sys.stderr)
        """

        with self.server.open(self.config_files["config.toml"], "r") as fp:
            cfg = tomlkit.load(fp)

            pub_api_port = urlparse("http://" + cfg["api"]["bind_public"]).port
            priv_api_port = urlparse("http://" + cfg["api"]["bind_private"]).port
            pub_grpc_port = urlparse("http://" + cfg["grpc"]["public"]["bind"]).port
            priv_grpc_port = urlparse("http://" + cfg["grpc"]["private"]["bind"]).port

            if (
                not pub_api_port
                or not priv_api_port
                or not pub_grpc_port
                or not priv_grpc_port
            ):
                raise RuntimeError("Could not get api & grpc port from config")

            if self.server.server_opts.massa:
                massa_server_opts: MassaNodeOpts = self.server.server_opts.massa
                self.pub_api2 = massa_jsonrpc_api.Api2(
                    "http://{}:{}".format(
                        self.server.host, massa_server_opts.jsonrpc_public_port
                    )
                )
                print("pub_api2 url:", self.pub_api2.url)
                self.priv_api2 = massa_jsonrpc_api.Api2(
                    "http://{}:{}".format(
                        self.server.host, massa_server_opts.jsonrpc_private_port
                    )
                )
                self.grpc_host = self.server.host
                self.pub_grpc_port = massa_server_opts.grpc_public_port
                self.pub_grpc_url = "{}:{}".format(self.server.host, pub_grpc_port)
                self.priv_grpc_port = massa_server_opts.grpc_private_port
                self.priv_grpc_url = "{}:{}".format(self.server.host, priv_grpc_port)

            else:
                self.pub_api2: Api2 = massa_jsonrpc_api.Api2(
                    "http://{}:{}".format(self.server.host, pub_api_port)
                )
                self.priv_api2 = massa_jsonrpc_api.Api2(
                    "http://{}:{}".format(self.server.host, priv_api_port)
                )
                self.grpc_host = self.server.host
                self.pub_grpc_port = pub_grpc_port
                self.pub_grpc_url = "{}:{}".format(self.server.host, pub_grpc_port)
                self.priv_grpc_port = priv_grpc_port
                self.priv_grpc_url = "{}:{}".format(self.server.host, priv_grpc_port)
            print("pub_api2 url:", self.pub_api2.url)

        cmd = " ".join(self.node_start_cmd)
        if args:
            args_joined = " ".join(args)
            if args_joined:
                cmd += " "
                cmd += args_joined

        print("cmd:", cmd)
        process = self.server.run(
            [cmd],
            cwd=self.install_folder / "massa-node",
            env=env,
            stdout=stdout,
            stderr=stderr,
        )
        with process as p:
            try:
                yield p
            except Exception:
                # Note: Need to catch every exception here as we need to stop subprocess.Popen
                #       otherwise it will wait forever
                #       so first print traceback then stop the process
                import traceback

                print(traceback.format_exc())
                self.stop(p)
                # Re Raise exception so test will be marked as failed
                raise
            else:
                # Note: normal end
                self.stop(p)

    def stop(self, process):
        """Stop a node

        Stop a Massa node but note that it is called automatically when the context manager of start() exits
        """

        # try to stop using the API
        try:
            self.priv_api2.stop_node()
        except (ConnectionRefusedError, requests.exceptions.ConnectionError):
            # node is stuck or already stopped - try to terminate the process
            self.server.stop(process)
        # else:
        #     # Note: sometimes the node take ages to end so we force the stop here too
        #     #       happens for subprocess.Popen
        #     self.server.stop(process)

    # Config

    # @contextmanager
    # def read_config(self):
    #     """ Read config.toml (as a context manager).
    #     """
    #     fp = self.server.open(self.config_files["config.toml"], "r")
    #     cfg = tomlkit.load(fp)
    #     try:
    #         yield cfg
    #     finally:
    #         fp.close()

    @contextmanager
    def edit_config(self) -> Generator[TOMLDocument, None, None]:
        """Edit config.toml (as a context manager). Must be called before start()"""
        # print("Editing config", self.config_path)
        fp = self.server.open(str(self.config_files["config.toml"]), "r+")
        cfg = tomlkit.load(fp)

        try:
            yield cfg
        finally:
            fp.seek(0)
            fp.truncate(0)
            tomlkit.dump(cfg, fp)
            # TODO: should try except seek / truncate / dump otherwise if failure, no close?
            fp.close()

        # print("is fp closed:", fp.closed)
        # print("end of edit_config")

    @contextmanager
    def edit_json(self, json_filepath: Path, mode: str = "r+", default_json=None):
        fp = self.server.open(json_filepath, mode)
        try:
            cfg = json.load(fp)
        except json.decoder.JSONDecodeError:
            # Json file is empty (json file just created?), return default value
            cfg = default_json

        try:
            yield cfg
        finally:
            fp.seek(0)
            fp.truncate(0)
            json.dump(cfg, fp)
            fp.close()

    # @contextmanager
    def edit_ledger(self):
        """Edit initial ledger"""

        return self.edit_json(self.config_files["initial_ledger.json"])

    def edit_initial_peers(self):
        """Edit initial peers

        Example:
            >>> from massa_test_framework import Server, ServerOpts, Node
            >>> server = Server(ServerOpts(local=True))
            >>> node = Node(server)
            >>> with node.edit_initial_peers() as peers:
            >>>    peers.clear()
        """
        return self.edit_json(self.config_files["initial_peers.json"])

    def edit_initial_deferred_credits(self):
        return self.edit_json(self.config_files["deferred_credits.json"])

    def edit_initial_rolls(self):
        return self.edit_json(self.config_files["initial_rolls.json"])

    def edit_node_privkey(self):
        return self.edit_json(
            self.config_files["node_privkey.key"],
            "w+",
            {"public_key": "", "secret_key": ""},
        )

    def edit_bootstrap_whitelist(self):
        return self.edit_json(self.config_files["bootstrap_whitelist.json"])

    # API

    def get_status(self):
        return self.pub_api2.get_status()

    def get_last_period(self) -> int:
        """Get last slot period for the node

        This a helper function calling (jsonrpc api) get_status() and extracting only the last slot period

        Returns:
             the period as integer
        """
        res = self.get_status()
        # print("res", res)
        return res["result"]["last_slot"]["period"]

    def get_addresses(self, addresses: List[str]) -> Dict[str, AddressInfo]:
        """Get addresses

        Returns:
            A dict with key -> Address string, value -> [AddressInfo](api.AddressInfo)
        """
        res_ = self.pub_api2.get_addresses(addresses)
        final_res = {}
        for res in res_["result"]:
            final_res[res["address"]] = AddressInfo(
                res["address"],
                res["thread"],
                float(res["final_balance"]),
                int(res["final_roll_count"]),
                float(res["candidate_balance"]),
                int(res["candidate_roll_count"]),
            )

        return final_res

    def add_staking_secret_keys(self, secret_keys: List[str]) -> None:
        res = self.priv_api2.add_staking_secret_keys(secret_keys)
        return res

    def send_operations(self, operations: List[bytes]) -> List[str]:
        """Send operations (like coin transfer)

        Send serialized operations using jsonrpc api

        Args:
            operations: a list of serialized operations

        Returns:
            If successful, returns a list of operation IDs.

        Raises:
            Exception: If send_operation return an error, an exception is raised with the error message.

        """
        res = self.pub_api2.send_operations(operations)

        err = res.get("error", None)
        if err is not None:
            msg = str(err.get("message", "Unknown error"))
            raise Exception(msg)

        return res["result"]

    def node_peers_whitelist(self):
        """Not implemented in Massa node"""
        res = self.priv_api2.node_peers_whitelist()
        print("node_peers_whitelist", res, type(res))
        return res

    def node_bootstrap_whitelist(self):
        """Not implemented in Massa node"""
        res = self.priv_api2.node_bootstrap_whitelist()
        print("node_bootstrap_whitelist", res, type(res))
        return res

    def get_stakers(self):
        res = self.pub_api2.get_stakers()
        print("get_stakers", res, type(res))
        return res

    # API GRPC

    async def _public_grpc_call(
        self, host: str, port: int, function_name: str, request: betterproto.Message
    ) -> betterproto.Message:
        # Note: asyncio.run will create a new event loop - channel must be created in this event loop
        #       that's why we need to have everything in this 'generic' function
        channel = Channel(host=host, port=port)
        service = PublicServiceStub(channel)
        f = getattr(service, function_name)
        result = await f(request)
        # Avoid warning message
        channel.close()
        return result

    async def _private_grpc_call(
        self, host: str, port: int, function_name: str, request: betterproto.Message
    ) -> betterproto.Message:
        # Note: asyncio.run will create a new event loop - channel must be created in this event loop
        #       that's why we need to have everything in this 'generic' function
        channel = Channel(host=host, port=port)
        service = PrivateServiceStub(channel)
        f = getattr(service, function_name)
        result = await f(request)
        # Avoid warning message
        channel.close()
        return result

    def get_version(self):
        request = GetStatusRequest()
        get_status_response: GetStatusResponse = asyncio.run(
            self._public_grpc_call(
                self.grpc_host, self.pub_grpc_port, "get_status", request
            )
        )
        return get_status_response.status.version

    def get_status_grpc(self):
        request = GetStatusRequest()
        get_status_response: GetStatusResponse = asyncio.run(
            self._public_grpc_call(
                self.grpc_host, self.pub_grpc_port, "get_status", request
            )
        )
        return get_status_response

    def get_mip_status(self) -> GetMipStatusResponse:
        request = GetMipStatusRequest()
        get_mip_status_response: GetMipStatusResponse = asyncio.run(
            self._private_grpc_call(
                self.grpc_host, self.priv_grpc_port, "get_mip_status", request
            )
        )
        return get_mip_status_response

    def query_state(self, query_state_request: QueryStateRequest) -> QueryStateResponse:
        """Queries the execution state of the node.

        Example::

            addr_bytecode_final_request = AddressBytecodeFinal(address=addr)
            execution_query_request = ExecutionQueryRequestItem(address_bytecode_final=addr_bytecode_final_request)
            query_state_request = QueryStateRequest(queries=[execution_query_request])

            res = node.query_state(query_state_request)
            print(res.responses[0].result.bytes)

        Args:
            query_state_request

        """

        query_state_response: QueryStateResponse = asyncio.run(
            self._public_grpc_call(
                self.grpc_host, self.pub_grpc_port, "query_state", query_state_request
            )
        )
        return query_state_response

    def get_stakers_grpc(self) -> GetStakersResponse:
        """Queries the gRPC GetStakers method.

        Example:
            res = node.get_stakers_grpc()
            print(res.stakers)

        """

        get_stakers_response: GetStakersResponse = asyncio.run(
            self._public_grpc_call(
                self.grpc_host, self.pub_grpc_port, "get_stakers", GetStakersRequest()
            )
        )

        return get_stakers_response

    def execute_read_only_call(
        self, request: ExecuteReadOnlyCallRequest
    ) -> ReadOnlyExecutionOutput:
        """
        Executes a read-only call using the specified request.

        Args:
            request (ExecuteReadOnlyCallRequest): The request object for the read-only call.

        Returns:
            ReadOnlyExecutionOutput: The output of the read-only call.
        """
        response: ExecuteReadOnlyCallResponse = asyncio.run(
            self._public_grpc_call(
                self.grpc_host,
                self.pub_grpc_port,
                "execute_read_only_call",
                request,
            )
        )
        return response.output

    def wait_ready(self, timeout: int = 20) -> None:
        """Wait for node to be ready

        Blocking wait for node to be ready

        Args:
            timeout: max number of seconds to wait for
        """

        # TODO: can take into account the GENESIS time? env var?

        done = False
        count = 0.0
        duration = 0.5

        while not done:
            try:
                self.get_last_period()
            except (TypeError, requests.exceptions.ConnectionError):
                # last slot is None - node has not yet fully started
                # sleep a while between each try
                time.sleep(duration)
                count += duration
                if count > timeout:
                    raise TimeoutError(f"Node is not ready after {timeout} seconds")
            else:
                done = True

    def wait_with_cb(
        self, cb: Callable[..., bool], timeout=20, sleep_duration=0.5
    ) -> None:
        """Wait for node with a custom callback function

        Args:
            timeout: max number of seconds to wait for
            cb: function to call, must return boolean, return if result is True
            sleep_duration: sleep duration in seconds between 2 cb calls
        Raise:
            TimeoutError: cb function did not return True after given timeout
        """

        done = False
        count = 0.0

        while not done:
            done = cb()
            if not done:
                time.sleep(sleep_duration)
                count += sleep_duration
                if count > timeout:
                    raise TimeoutError(f"Timeout after {timeout} seconds")
