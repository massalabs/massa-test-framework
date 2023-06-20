from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

from typing import Optional, List, Dict

from massa_test_framework.server import Server

import patch_ng


class BuildKind(StrEnum):
    Debug = "debug"
    Release = "release"


@dataclass
class CompileOpts:
    git_url: Optional[str] = "https://github.com/massalabs/massa.git"
    # Clone (git clone) option
    clone_opts: List[str] = field(default_factory=list)
    # Build (Compile) option (e.g. for cargo build)
    build_opts: List[str] = field(default_factory=list)
    cargo_bin: str = "cargo"
    already_compiled: Optional[Path] = None
    config_files: Dict[str, Path] = field(
        default_factory=lambda: {
            "config.toml": Path("massa-node/base_config/config.toml"),
            "initial_ledger.json": Path("massa-node/base_config/initial_ledger.json"),
            "initial_peers.json": Path("massa-node/base_config/initial_peers.json"),
            "initial_rolls.json": Path("massa-node/base_config/initial_rolls.json"),
            "initial_vesting.json": Path("massa-node/base_config/initial_vesting.json"),
            "bootstrap_whitelist.json": Path(
                "massa-node/base_config/bootstrap_whitelist.json"
            ),
            "node_privkey.key": Path("massa-node/config/node_privkey.key"),
            "abi_gas_costs.json": Path(
                "massa-node/base_config/gas_costs/abi_gas_costs.json"
            ),
            "wasm_gas_costs.json": Path(
                "massa-node/base_config/gas_costs/wasm_gas_costs.json"
            ),
        }
    )


class CompileUnit:
    def __init__(self, server: Server, compile_opts: CompileOpts):
        """ Init a CompileUnit object

        Notes:
             Can be shared to multiple [Node](massa_test_framework.Node) objects \
             (e.g. Only 1 compilation for all nodes used in a test)
        """
        self.server = server
        self.compile_opts = compile_opts

        self._repo = ""
        self._patches: Dict[str, str | Path] = {}

    def compile(self) -> None:
        """Clone, apply patches if any then compile

        Raise:
            RuntimeError: if git clone return non 0, cargo build return non 0, patch cannot be applied
        """
        tmp_folder = self.server.mkdtemp(prefix="compile_massa_")
        # print(self.compile_opts)
        # print(type(self.compile_opts))
        cmd = ["git", "clone"]
        cmd.extend(self.compile_opts.clone_opts)
        cmd.extend([str(self.compile_opts.git_url), str(tmp_folder)])
        print(f"Cloning repo, using cmd ${cmd=}...")

        # Note: need to join cmd otherwise it will fail
        with self.server.run([" ".join(cmd)]) as proc:
            proc.wait()
            print("Done.")

        # print("return code", proc.returncode)
        if proc.returncode != 0:
            # TODO: custom exception like CloneError
            raise RuntimeError(
                f"Could not clone {self.compile_opts.git_url} to {tmp_folder}, return code: {proc.returncode}"
            )

        # TODO: cleanup if apply fails?
        for patch_name, patch in self._patches.items():
            print(f"Applying patch {patch_name}")
            if isinstance(patch, Path):
                patchset = patch_ng.fromfile(patch)
            else:
                patchset = patch_ng.fromstring(patch)

            res = patchset.apply(root=tmp_folder)
            if not res:
                raise RuntimeError(
                    f"Could not apply patch {patch_name} ({patch.absolute()}) to repo: {tmp_folder}"
                )
            print("Done.")

        build_cmd = [self.compile_opts.cargo_bin, "build"]
        # print(self.compile_opts.build_opts)
        build_cmd.extend(self.compile_opts.build_opts)
        with self.server.run([" ".join(build_cmd)], cwd=str(tmp_folder)) as proc:
            proc.wait()
            print("Done.")

        # print("return code", proc.returncode)
        if proc.returncode != 0:
            # TODO: custom exception like CompilationError
            raise RuntimeError("Could not build")

        self._repo = Path(tmp_folder)

    def add_patch(self, patch_name: str, patch: bytes | Path) -> None:
        """ Add patch to apply after cloning

        Args:
            patch_name: a meaningful name or description
            patch: a patch file or binary data of a patch

        Notes:
            Patch must be generated as unified patch (e.g. git diff --unified > foo.patch)
        """
        self._patches[patch_name] = patch

    @property
    def repo(self):
        if self.compile_opts.already_compiled:
            return self.compile_opts.already_compiled
        else:
            return self._repo

    @property
    def build_kind(self) -> BuildKind:
        if "--release" in self.compile_opts.build_opts:
            return BuildKind.Release
        else:
            return BuildKind.Debug

    @property
    def massa_node(self) -> Path:
        """Relative path (relative to compilation folder) to massa node binary"""
        return Path(f"target/{self.build_kind}/massa-node")

    @property
    def config_files(self) -> Dict[str, Path]:
        return self.compile_opts.config_files
