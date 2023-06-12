from dataclasses import dataclass, field
from pathlib import Path

from typing import Optional, List

from massa_test_framework.server import Server


@dataclass
class CompileOpts:
    git_url: Optional[str] = "https://github.com/massalabs/massa.git"
    # Build (Compile) option (e.g. for cargo build)
    build_opts: List[str] = field(default_factory=list)
    already_compiled: Optional[Path] = None


class CompileUnit:
    def __init__(self, server: Server, compile_opts: CompileOpts):
        self.server = server
        self.compile_opts = compile_opts

        self._repo = ""

    def compile(self):
        tmp_folder = self.server.mkdtemp(prefix="compile_massa_")
        # print(self.compile_opts)
        # print(type(self.compile_opts))
        cmd = ["git", "clone", str(self.compile_opts.git_url), str(tmp_folder)]
        # cmd = ["git", "clone", "/home/sydh/dev/massa6", "/tmp/cu_12345"]
        print(f"Cloning repo, using cmd ${cmd=}...")
        # print([type(i) for i in cmd])
        # TODO: raise if cmd fails, check return code?
        # Note: need to join cmd otherwise it will fail
        with self.server.run([" ".join(cmd)]) as proc:
            print("Done.")

        print("return code", proc.returncode)
        if proc.returncode != 0:
            # TODO: custom exception like CloneError
            raise RuntimeError(
                f"Could not clone {self.compile_opts.git_url} to {tmp_folder}, return code: {proc.returncode}"
            )

        build_cmd = ["cargo", "build"]
        print(self.compile_opts.build_opts)
        build_cmd.extend(self.compile_opts.build_opts)
        with self.server.run([" ".join(build_cmd)], cwd=tmp_folder) as proc:
            print("Done.")

        print("return code", proc.returncode)
        if proc.returncode != 0:
            # TODO: custom exception like CompilationError
            raise RuntimeError("Could not build")

        self._repo = Path(tmp_folder)

    def repo(self):
        # TODO: read property
        if self.compile_opts.already_compiled:
            return self.compile_opts.already_compiled
        else:
            return self._repo
