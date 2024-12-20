from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
import re
import copy

from typing import Optional, List, Dict

from massa_test_framework.server import Server

import patch_ng


@dataclass
class PatchConstant:
    constant_name: str
    new_value: str
    constant_type: Optional[str]
    constant_file: Optional[Path]

    def apply(self, root=Path, strip: int = 0, fuzz: bool = False):
        # pub const MIP_STORE_STATS_BLOCK_CONSIDERED: usize = 1000;
        # -->
        # pub const MIP_STORE_STATS_BLOCK_CONSIDERED: usize = 10;

        print("f matching (.* const {self.constant_name}[ :].*) = (.*);")
        with open(root / self.constant_file, "r+") as fp:
            content = fp.read()
            content_sub = re.sub(
                f"(.* const {self.constant_name}[ :].*) = (.*);",
                f"\g<1> = {self.new_value};",
                content,
            )
            fp.seek(0)
            fp.truncate(0)
            fp.write(content_sub)

        return True


class BuildKind(StrEnum):
    Debug = "debug"
    Release = "release"


@dataclass
class CompileOpts:
    # TODO: rename to clone_from? can be a path too + typing Path | url ?
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
            # "initial_vesting.json": Path("massa-node/base_config/initial_vesting.json"),
            "deferred_credits.json": Path(
                "massa-node/base_config/deferred_credits.json"
            ),
            "node_privkey.key": Path("massa-node/config/node_privkey.key"),
            "abi_gas_costs.json": Path(
                "massa-node/base_config/gas_costs/abi_gas_costs.json"
            ),
            "client/config.toml": Path("massa-client/base_config/config.toml"),
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

        self._repo: Path = Path("")
        self._target = ""
        self._patches: Dict[str, bytes | str | Path | PatchConstant] = {}

    @staticmethod
    def from_compile_unit(cu: "CompileUnit", repo_sync: bool = False) -> "CompileUnit":
        """Create a new CompileUnit from another one

        Set repo_sync to True in order to clone from folder thus having two identical repo.
        Can be useful if you clone from a repo using a branch and someone push
        some changes between the 2 clones.

        Args:
            cu: the original compile unit object
            repo_sync: If True, will clone from cu clone folder

        Return:
            A new CompileUnit
        """

        new_compile_opts = copy.copy(cu.compile_opts)
        if repo_sync:
            new_compile_opts.git_url = cu.repo

        return CompileUnit(server=cu.server, compile_opts=new_compile_opts)

    def compile(self) -> None:
        """Clone, apply patches if any then compile

        Raise:
            RuntimeError: if git clone return non 0, cargo build return non 0, patch cannot be applied
        """
        # build or rebuild into the predefined directory
        if self.compile_opts.already_compiled is not None:
            # assuming we are in compile it means me want to rebuild
            # and reuse the same folder
            # TODO: if the folder exists do a git pull instead of clone
            # for now we assume the user just want to reuse he folder name
            tmp_folder = self.compile_opts.already_compiled
            if tmp_folder.exists():
                self.server.rmtree(str(tmp_folder))
            #self.server.mkdir(tmp_folder)
        else: # use a temporary folder
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
            elif isinstance(patch, str):
                patchset = patch_ng.fromstring(patch)
            else:
                patchset = patch  # PatchConstant

            if isinstance(patchset, bool) and not patchset:
                # patch_ng.fromfile or .fromstring return False on parse error
                raise RuntimeError("Could not parse patch:", patch)

            res = patchset.apply(root=tmp_folder, fuzz=True)
            if not res:
                raise RuntimeError(
                    f"Could not apply patch {patch_name} ({patch!r}) to repo: {tmp_folder}"
                )
            print("Done.")

        build_cmd_ = [self.compile_opts.cargo_bin, "build"]
        # print(self.compile_opts.build_opts)
        build_cmd_.extend(self.compile_opts.build_opts)
        build_cmd = " ".join(build_cmd_)
        print("Build cmd:", build_cmd)
        with self.server.run([build_cmd], cwd=str(tmp_folder)) as proc:
            proc.wait()
            print("Done.")

        # print("return code", proc.returncode)
        if proc.returncode != 0:
            # TODO: custom exception like CompilationError?
            raise RuntimeError("Could not build")

        if "--target" in build_cmd:
            # if --target is specified, path is like: target/{TARGET_NAME}/debug/[...]
            rg_res = re.search("--target ([\w-]+)", build_cmd)
            if not rg_res:
                raise RuntimeError("Cannot match arch from --target")
            self._repo = Path(tmp_folder)
            self._target = rg_res.group(1)
        else:
            # No --target, path is like: target/debug/[...]
            self._repo = Path(tmp_folder)
            self._target = ""

    def add_patch(self, patch_name: str, patch: bytes | Path | PatchConstant) -> None:
        """Add patch to apply after cloning

        Args:
            patch_name: a meaningful name or description
            patch: a patch file or binary data of a patch

        Notes:
            Patch must be generated as unified patch (e.g. git diff --unified > foo.patch)
        """

        self._patches[patch_name] = patch

    def add_patch_constant(
        self,
        constant_name: str,
        new_value: str,
        constant_type: Optional[str] = None,
        constant_file: Optional[Path] = Path("massa-models/src/config/constants.rs"),
    ):
        """Add a patch updating a constant value in a rust file

        Args:
            constant_name: const to update
            new_value: ;)
            constant_type: optional const type in rust file
            constant_file: optional path
        """
        self._patches[f"patch_{constant_name}_to_{new_value}"] = PatchConstant(
            constant_name, new_value, constant_type, constant_file
        )

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

    def bin_path(self, bin_name: str):
        """Relative path (relative to compilation folder) to (rust compiled) binary"""
        if self._target:
            return Path(f"target/{self._target}/{self.build_kind}/{bin_name}")
        else:
            return Path(f"target/{self.build_kind}/{bin_name}")

    @property
    def massa_node(self) -> Path:
        """Relative path (relative to compilation folder) to massa node binary"""
        return self.bin_path("massa-node")

    @property
    def massa_client(self) -> Path:
        """Relative path (relative to compilation folder) to massa client binary"""
        return self.bin_path("massa-client")

    @property
    def massa_ledger_editor(self) -> Path:
        return self.bin_path("massa-ledger-editor")

    @property
    def config_files(self) -> Dict[str, Path]:
        return self.compile_opts.config_files
