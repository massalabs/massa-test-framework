import sys
from pathlib import Path
from contextlib import contextmanager

from typing import Dict, Optional, List

from massa_test_framework.compile import CompileUnit, CompileOpts
from massa_test_framework.server import Server
from massa_test_framework.remote import copy_file, RemotePath


# TODO: facto with Node
class LedgerEditor:
    def __init__(self, server: Server, compile_unit: CompileUnit):
        """Init a massa ledger editor object"""

        self.server = server
        self.compile_unit = compile_unit

        self._to_install: Dict[str, Path] = {
            "massa-ledger-editor": self.compile_unit.massa_ledger_editor,
        }
        self._to_install.update(self.compile_unit.config_files)
        self._to_create: List[str] = []

        self.start_cmd = ["./massa-ledger-editor"]
        self.stop_cmd = ""

        # setup
        self.install_folder = self._install()

    def _install(self) -> Path | RemotePath:
        tmp_folder = self.server.mkdtemp(prefix="massa_ledger_editor_")
        repo = self.compile_unit.repo

        for to_create in self._to_create:
            f = Path(tmp_folder) / to_create
            self.server.mkdir(Path(f))

        for filename, to_install in self._to_install.items():
            src = repo / to_install
            if filename == "massa-ledger-editor":
                dst = tmp_folder
            else:
                dst = tmp_folder / to_install
            self.server.mkdir(dst.parent)
            copy_file(src, dst)

        return tmp_folder

    @staticmethod
    def from_compile_unit(server: Server, compile_unit: CompileUnit) -> "LedgerEditor":
        node = LedgerEditor(server, compile_unit)
        return node

    @staticmethod
    def from_dev(
        server: Server, repo: Path, build_opts: Optional[List[str]] = None
    ) -> "LedgerEditor":
        compile_opts = CompileOpts()
        compile_opts.already_compiled = repo
        if build_opts:
            compile_opts.build_opts = build_opts
        cu = CompileUnit(server, compile_opts)
        node = LedgerEditor(server, cu)
        return node

    @contextmanager
    def start(
        self,
        env: Optional[Dict[str, str]] = None,
        args: Optional[List[str]] = None,
        stdout=sys.stdout,
        stderr=sys.stderr,
    ):
        """Run Massa ledger editor

        Run massa ledger editor (as a context manager)

        Args:
            env:
            args: additional node arguments (e.g. ["--restart-from-snapshot-at-period", "10"])
            stdout: where to log node standard output (default to sys.stdout)
            stderr: where to log node standard error output (default to sys.stderr)
        """

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
