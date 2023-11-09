import sys
from contextlib import contextmanager
from pathlib import Path
from dataclasses import dataclass

from typing import Optional, Dict, List

from .server import Server
from .compile import CompileUnit, CompileOpts
from .remote import RemotePath, copy_file


@dataclass
class SrcDst:
    """Source and Destination paths (usually for copy)"""
    src: Path
    dst: Path


class RemoteBin:

    def __init__(self, server: Server, compile_unit: CompileUnit):

        # Dummy code so the IDE is happy
        self.server = server
        self.compile_unit = compile_unit
        self.start_cmd = [""]

        # self.install_folder = self._install(...)
        raise NotImplementedError

    def _install(self, to_install: Dict[str, Path | SrcDst], tmp_prefix: str = "remote_bin") -> Path | RemotePath:

        """
        Args:
            to_install: a dict of key (filename), path (relative path in install folder)
        """

        tmp_folder = self.server.mkdtemp(prefix="remote_bin_")
        repo = self.compile_unit.repo

        for filename, to_install_item in to_install.items():
            if isinstance(to_install_item, SrcDst):
                src = repo / to_install_item.src
                dst = tmp_folder / to_install_item.dst
            else:
                src = repo / to_install_item
                dst = tmp_folder / to_install

            print("server mkdir:", dst.parent)
            self.server.mkdir(dst.parent)
            print(f"copy_file {src} -> {dst}")
            copy_file(src, dst)

        return tmp_folder

    @classmethod
    def from_compile_unit(cls, server: Server, compile_unit: CompileUnit) -> "RemoteBin":
        node = cls(server, compile_unit)
        return node

    @classmethod
    def from_dev(
            cls, server: Server, repo: Path, build_opts: Optional[List[str]] = None
    ) -> "RemoteBin":
        compile_opts = CompileOpts()
        compile_opts.already_compiled = repo
        if build_opts:
            compile_opts.build_opts = build_opts
        cu = CompileUnit(server, compile_opts)
        node = cls(server, cu)
        return node

    @contextmanager
    def start(
            self,
            env: Optional[Dict[str, str]] = None,
            args: Optional[List[str]] = None,
            stdout=sys.stdout,
            stderr=sys.stderr,
    ):
        cmd = " ".join(self.start_cmd)
        if args:
            args_joined = " ".join(args)
            if args_joined:
                cmd += " "
                cmd += args_joined

        print(f"{cmd=}")
        process = self.server.run(
            [cmd],
            cwd=str(self.install_folder),
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
        pass
