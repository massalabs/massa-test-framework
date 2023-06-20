import sys
import asyncio
from contextlib import contextmanager
from pathlib import Path
import json
import time
from urllib.parse import urlparse

from typing import List, Dict, Optional

import betterproto
from grpclib.client import Channel

# internal
from massa_test_framework import massa_jsonrpc_api
from massa_test_framework.massa_grpc.massa.api.v1 import (
    GetVersionRequest,
    MassaServiceStub,
    GetVersionResponse,
    GetMipStatusRequest,
    GetMipStatusResponse,
)
from massa_test_framework.massa_jsonrpc_api import AddressInfo
from massa_test_framework.compile import CompileUnit, CompileOpts
from massa_test_framework.remote import copy_file, RemotePath
from massa_test_framework.server import Server

# third party
import requests
import tomlkit


class Node:
    def __init__(self, server: Server, compile_unit: CompileUnit):
        """Init a Node (e.g. a Massa Node) object

        The new node can be started, stopeed, edited (various config files)

        Args:
            server: the server on which the node will run on
            compile_unit: the compilation of the massa repo

        Raises:
            RuntimeError: if api ports && grpc port cannot be read from config

        """


        self.server = server
        self.compile_unit = compile_unit

        # self.to_install = [
        #    ("target/release/massa-node", ""),
        #    ("massa-node/base_config/config.toml", "base_config"),
        #    ("massa-node/base_config/initial_ledger.json", "base_config"),
        #    ("massa-node/base_config/initial_peers.json", "base_config"),
        #    ("massa-node/base_config/initial_rolls.json", "base_config"),
        #    ("massa-node/base_config/initial_vesting.json", "base_config"),
        #    (
        #        "massa-node/base_config/gas_costs/abi_gas_costs.json",
        #        "base_config/gas_costs",
        #    ),
        #    (
        #        "massa-node/base_config/gas_costs/wasm_gas_costs.json",
        #        "base_config/gas_costs",
        #    ),
        # ]

        self._to_install: Dict[str, Path] = {
            "massa_node": self.compile_unit.massa_node,
        }
        self._to_install.update(self.compile_unit.config_files)
        self._to_create = ["massa-node", "massa-node/config", "massa-client"]

        self.node_start_cmd = ["./massa-node", "-p", "1234"]
        self.node_stop_cmd = ""

        # TODO: build this from config?
        # if self.server.server_opts.local:
        #     # self.pub_api = massa_jsonrpc_api.Api("http://127.0.0.1:33035")
        #     # self.priv_api = massa_jsonrpc_api.Api("http://127.0.0.1:33034")
        #     self.pub_api2 = massa_jsonrpc_api.Api2("http://127.0.0.1:33035")
        #     self.priv_api2 = massa_jsonrpc_api.Api2("http://127.0.0.1:33034")
        #     # self.priv_api2 = massa_jsonrpc_api.Api2("http://127.0.0.1:33034")
        #     self.grpc_url = "127.0.0.1:33037"
        # else:
        #     self.pub_api2 = massa_jsonrpc_api.Api2(
        #         "http://{}:33035".format(self.server.server_opts.ssh_host)
        #     )
        #     self.priv_api2 = massa_jsonrpc_api.Api2(
        #         "http://{}:33034".format(self.server.server_opts.ssh_host)
        #     )
        #     self.grpc_url = "{}:33037".format(self.server.server_opts.ssh_host)
        # TODO: grpc api

        # setup node
        self.install_folder = self._install()
        self.config_files = {
            k: self.install_folder / p
            for k, p in self.compile_unit.config_files.items()
        }

        # print(self.config_files)

        with self.server.open(self.config_files["config.toml"], "r") as fp:
            cfg = tomlkit.load(fp)

            pub_api_port = urlparse("http://" + cfg["api"]["bind_public"]).port
            priv_api_port = urlparse("http://" + cfg["api"]["bind_private"]).port
            grpc_port = urlparse("http://" + cfg["grpc"]["bind"]).port

            if not pub_api_port or not priv_api_port or not grpc_port:
                raise RuntimeError("Could not get api & grpc port from config")

            self.pub_api2 = massa_jsonrpc_api.Api2(
                "http://{}:{}".format(self.server.host, pub_api_port)
            )
            self.priv_api2 = massa_jsonrpc_api.Api2(
                "http://{}:{}".format(self.server.host, priv_api_port)
            )
            self.grpc_url = "{}:{}".format(self.server.host, grpc_port)

        # TODO: can we have a dict: to_install and query this dict?
        # self.config_path = Path(self.install_folder, "base_config/config.toml")
        # self.initial_ledger_path = Path(
        #     self.install_folder, "base_config/initial_ledger.json"
        # )
        # self.initial_peers_path = Path(
        #     self.install_folder, "base_config/initial_peers.json"
        # )
        # self.initial_rolls_path = Path(
        #     self.install_folder, "base_config/initial_rolls.json"
        # )
        # self.node_privkey_path = Path(
        #     self.install_folder, "config/node_privkey.key"
        # )

        #

    # def _install(self):
    #     tmp_folder = self.server.mkdtemp(prefix="massa_")
    #     print("Installing to tmp folder", tmp_folder)
    #     repo = self.compile_unit.repo()
    #     print("repo", repo)

    #     for to_create in self.to_create:
    #         f = Path(tmp_folder) / to_create
    #         print(f"Creating {f}")
    #         self.server.mkdir(Path(f))

    #     print("to_install...")

    #     for to_install, dst_rel_folder in self.to_install:
    #         # TODO / FIXME
    #         # p = self.node.path_join(repo, to_install)
    #         p = repo / to_install
    #         dst = Path(tmp_folder)
    #         if dst_rel_folder:
    #             dst /= dst_rel_folder

    #         self.server.mkdir(dst)

    #         dst /= Path(to_install).name
    #         print(f"Copying {p} -> {dst} ...")
    #         self.server.send_file(p, dst)

    #     return tmp_folder

    def _install(self) -> Path | RemotePath:
        tmp_folder = self.server.mkdtemp(prefix="massa_")
        repo = self.compile_unit.repo

        for to_create in self._to_create:
            f = Path(tmp_folder) / to_create
            # print(f"Creating {f}")
            self.server.mkdir(Path(f))

        for filename, to_install in self._to_install.items():
            src = repo / to_install

            if filename == "massa_node":
                dst = tmp_folder / "massa-node" / to_install.name
            elif filename == "node_privkey.key":
                continue
            else:
                dst = tmp_folder / to_install
            # print("Creating folder", dst.parent)
            self.server.mkdir(dst.parent)
            # print("is dst a remote path?", isinstance(dst, RemotePath))
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
        self, env: Optional[Dict[str, str]] = None, stdout=sys.stdout, stderr=sys.stderr
    ):
        """Start a node

        Start a Massa node (as a context manager)
        """
        process = self.server.run(
            [" ".join(self.node_start_cmd)],
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
    def edit_config(self):
        """Edit config.toml (as a context manager). Must be called before start()"""
        # print("Editing config", self.config_path)
        fp = self.server.open(self.config_files["config.toml"], "r+")
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
        """Edit initial ledger
        """

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
        """Send operations using jsonrpc api

        Args:
            operations: a list of serialized operations
        Returns:
            a list of operation id
        """
        res = self.pub_api2.send_operations(operations)
        return res["result"]

    # API GRPC

    async def _grpc_call(
        self, host: str, port: int, function_name: str, request: betterproto.Message
    ) -> betterproto.Message:
        # Note: asyncio.run will create a new event loop - channel must be created in this event loop
        #       that's why we need to have everything in this 'generic' function
        channel = Channel(host=host, port=port)
        service = MassaServiceStub(channel)
        f = getattr(service, function_name)
        result = await f(request)
        # Avoid warning message
        channel.close()
        return result

    def get_version(self) -> str:
        request = GetVersionRequest(id="0")
        get_version_response: GetVersionResponse = asyncio.run(
            self._grpc_call("127.0.0.1", 33037, "get_version", request)
        )
        return get_version_response.version

    def get_mip_status(self) -> GetMipStatusResponse:
        request = GetMipStatusRequest(id="0")
        get_mip_status_response: GetMipStatusResponse = asyncio.run(
            self._grpc_call("127.0.0.1", 33037, "get_mip_status", request)
        )
        return get_mip_status_response

    #
    def wait_ready(self, timeout=20) -> None:
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
