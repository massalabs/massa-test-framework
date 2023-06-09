from contextlib import contextmanager
from pathlib import Path
import json
import time

from typing import List, Dict

# internal
from massa_test_framework import massa_jsonrpc_api
from massa_test_framework.massa_jsonrpc_api import AddressInfo
from massa_test_framework.compile import CompileUnit, CompileOpts
from massa_test_framework.server import Server

# third party
import requests
import tomlkit


class Node:
    def __init__(self, server: Server, compile_unit: CompileUnit):
        self.server = server
        self.compile_unit = compile_unit
        self.to_install = [
            ("target/release/massa-node", ""),
            ("massa-node/base_config/config.toml", "base_config"),
            ("massa-node/base_config/initial_ledger.json", "base_config"),
            ("massa-node/base_config/initial_peers.json", "base_config"),
            ("massa-node/base_config/initial_rolls.json", "base_config"),
            ("massa-node/base_config/initial_vesting.json", "base_config"),
            (
                "massa-node/base_config/gas_costs/abi_gas_costs.json",
                "base_config/gas_costs",
            ),
            (
                "massa-node/base_config/gas_costs/wasm_gas_costs.json",
                "base_config/gas_costs",
            ),
        ]
        self.to_create = ["config"]
        self.node_start_cmd = ["./massa-node", "-p", "1234"]
        self.node_stop_cmd = ""

        # TODO: build this from config?
        if self.server.server_opts.local:
            self.pub_api = massa_jsonrpc_api.Api("http://127.0.0.1:33035")
            self.priv_api = massa_jsonrpc_api.Api("http://127.0.0.1:33034")
            self.pub_api2 = massa_jsonrpc_api.Api2("http://127.0.0.1:33035")
            self.priv_api2 = massa_jsonrpc_api.Api2("http://127.0.0.1:33034")
        else:
            self.pub_api = massa_jsonrpc_api.Api(
                "http://{}:33035".format(self.server.server_opts.ssh_host)
            )
            self.priv_api = massa_jsonrpc_api.Api(
                "http://{}:33034".format(self.server.server_opts.ssh_host)
            )

        # TODO: grpc api

        # setup node
        self.install_folder = self._install()
        # TODO: can we have a dict: to_install and query this dict?
        self.config_path = Path(self.install_folder, "base_config/config.toml")
        self.initial_ledger_path = Path(
            self.install_folder, "base_config/initial_ledger.json"
        )
        self.initial_peers_path = Path(
            self.install_folder, "base_config/initial_peers.json"
        )
        self.initial_rolls_path = Path(
            self.install_folder, "base_config/initial_rolls.json"
        )

        #

    def _install(self):
        tmp_folder = self.server.mkdtemp(prefix="massa_")
        print("Installing to tmp folder", tmp_folder)
        repo = self.compile_unit.repo()
        print("repo", repo)

        for to_create in self.to_create:
            f = Path(tmp_folder) / to_create
            print(f"Creating {f}")
            self.server.mkdir(Path(f))

        print("to_install...")

        for to_install, dst_rel_folder in self.to_install:
            # TODO / FIXME
            # p = self.node.path_join(repo, to_install)
            p = repo / to_install
            dst = Path(tmp_folder)
            if dst_rel_folder:
                dst /= dst_rel_folder

            self.server.mkdir(dst)

            dst /= Path(to_install).name
            print(f"Copying {p} -> {dst} ...")
            self.server.send_file(p, dst)

        return tmp_folder

    @staticmethod
    def from_compile_unit(server: Server, compile_unit: CompileUnit):
        node = Node(server, compile_unit)
        return node

    @staticmethod
    def from_dev(server: Server, repo: Path):
        # TODO: add options to recompile?
        compile_opts = CompileOpts()
        compile_opts.already_compiled = repo
        cu = CompileUnit(server, compile_opts)
        node = Node(server, cu)
        return node

    @contextmanager
    def start0(self):
        process = self.server.run(
            [" ".join(self.node_start_cmd)], cwd=self.install_folder
        )
        print("[node start] process type:", type(process))
        try:
            print("[node start] yield", process)
            # Note: Subprocess.Popen execute as soon as it is instantiated and return an object
            #       while ParamikoRemotePopen.run return a context manager (and it must be used, using 'with')
            if hasattr(process, "__enter__"):
                with process as p:
                    yield p
            else:
                yield process
        finally:
            print("[node start] will stop", process)
            self.stop(process)

    @contextmanager
    def start(self):
        process = self.server.run(
            [" ".join(self.node_start_cmd)], cwd=self.install_folder
        )
        with process as p:
            try:
                yield p
            except Exception as e:
                # Note: Need to catch every exception here as we need to stop subprocess.Popen
                #       otherwise it will wait forever
                #       so first print traceback then stop the process
                import traceback

                print(traceback.format_exc())
                self.stop(p)
            else:
                # Note: normal end
                self.stop(p)

    def stop(self, process):
        # try to stop using the API
        try:
            self.priv_api.stop_node()
        except (ConnectionRefusedError, requests.exceptions.ConnectionError) as e:
            # node is stuck or already stopped - try to terminate the process
            self.server.stop(process)

    # Config

    @contextmanager
    def edit_config(self):
        print("Editing config", self.config_path)
        fp = self.server.open(self.config_path, "r+")
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
    def edit_json(self, json_filepath: Path):
        fp = self.server.open(json_filepath, "r+")
        cfg = json.load(fp)
        try:
            yield cfg
        finally:
            fp.seek(0)
            fp.truncate(0)
            json.dump(cfg, fp)
            fp.close()

    # @contextmanager
    def edit_ledger(self):
        # TODO: generic func over all json files?
        # fp = self.server.open(self.initial_ledger_path, "r+")
        # cfg = json.load(fp)
        # try:
        #     yield cfg
        # finally:
        #     fp.seek(0)
        #     fp.truncate(0)
        #     json.dump(cfg, fp)
        #     fp.close()
        return self.edit_json(self.initial_ledger_path)

    def edit_initial_peers(self):
        return self.edit_json(self.initial_peers_path)

    def edit_initial_rolls(self):
        return self.edit_json(self.initial_rolls_path)

    # API

    def get_status(self):
        return self.pub_api.get_status()

    def get_last_period(self):
        """Get last slot period for the node

        This a helper function calling (jsonrpc api) get_status() and extracting only the last slot period

        :return: the period as XXX
        """
        res = self.get_status()
        # Return period as int / str? TODO: typing
        return res["result"]["last_slot"]["period"]

    def get_addresses(self, addresses: List[str]) -> Dict[str, AddressInfo]:
        # TODO: design a better jsonrpc API
        # headers, payload = self.pub_api._api.get_addresses(addresses)
        # res_ = self.pub_api._make_request(headers, payload)

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

    def add_staking_secret_keys(self, secret_keys: List[str]):
        headers, payload = self.priv_api._api.add_staking_secret_keys(secret_keys)
        res = self.priv_api._make_request(headers, payload)
        return res

    def send_operations(self, operations: List[bytes]) -> List[str]:
        """Send operations using jsonrpc api
        :param operations: a list of serialized operations
        :return: a list of operation id
        """
        headers, payload = self.pub_api._api.send_operations(operations)
        res = self.pub_api._make_request(headers, payload)
        print("res", res)
        return res["result"]

    # API GRPC
    # TODO

    #
    def wait_ready(self, timeout=20):
        """Wait for node to be ready

        Blocking wait for node to be ready
        :param timeout: max number of seconds to wait for
        """

        # TODO: can take into account the GENESIS time?

        done = False
        count = 0.0
        duration = 0.5

        while not done:
            try:
                # print("Caling get_last_period...")
                self.get_last_period()
            except (TypeError, requests.exceptions.ConnectionError) as e:
                # last slot is None - node has not yet fully started
                # sleep a while between each try
                time.sleep(duration)
                count += duration
                if count > timeout:
                    raise TimeoutError(f"Node is not ready after {timeout} seconds")
            else:
                print("wait_ready is all done!")
                done = True
