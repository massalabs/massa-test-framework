from dataclasses import dataclass
from contextlib import contextmanager
from threading import Thread
import io
import time
import sys
from pathlib import Path
import datetime
import shutil
import subprocess
import tempfile
import os

from typing import List, Optional, BinaryIO, TextIO, Dict

import paramiko
from paramiko.sftp_client import SFTPFile, SFTPClient
from paramiko.channel import Channel

from massa_test_framework.remote import RemotePath


@dataclass
class ServerOpts:
    local: bool = False
    name: str = ""
    ssh_host: str = ""
    ssh_port: int = 22
    ssh_user: str = ""
    ssh_pwd: str = ""


class ParamikoRemotePopen:
    def __init__(self, channel: Channel):
        self.channel: Channel = channel

        self.channel.set_combine_stderr(True)
        self.channel.get_pty()

        self.returncode = -1

    @contextmanager
    def run(self, cmd, stdout: BinaryIO | TextIO):
        # Create a background thread to output result to a file
        bgthd = Thread(
            target=ParamikoRemotePopen.output_fp,
            name="run",
            args=[self.channel, stdout],
        )
        bgthd.daemon = True
        # print("Starting thread")
        bgthd.start()

        # self.channel.setblocking(0)
        # self.channel.settimeout(0.1)

        # if env:
        #     for env_var, env_value in env.items():
        #         print(f"Setting env: {env_var} - env_value: {env_value}")
        #         self.channel.set_environment_variable(env_var, env_value)

        # print("Exec command in channel")
        self.channel.exec_command(cmd)
        # session.setblocking(0)
        # session.settimeout(0.1)

        try:
            yield self
        finally:
            # print("[ParamikoRemotePopen - run] Exiting the context manager")
            self.channel.eof_received = True
            # Wait for thread to exit

            # print("Joining the background thread")
            bgthd.join(1)

            self.returncode = self.channel.exit_status
            # print("[ParamikoRemotePopen] self.returnode", self.returncode)
            # print("[ParamikoRemotePopen] self", self)

    @classmethod
    def output_fp(cls, channel: Channel, fp: BinaryIO | TextIO = sys.stdout):
        # print("Starting thread output_fp")
        done = False
        while not done:
            if channel.exit_status_ready() or channel.eof_received:
                # print("has exit status ready", channel.exit_status_ready())
                # print("has eof received", channel.eof_received)

                done = True

                # On exit, wait for ~ 1s (time to read remaining in stdout/stderr)
                start = time.perf_counter()
                while True:
                    if channel.recv_ready():
                        # fp.write(channel.recv(65535))
                        # print(channel.recv(65535))
                        buf = channel.recv(65535)
                        if isinstance(fp, io.TextIOBase):
                            fp.write(buf.decode())
                        else:
                            fp.write(buf)
                    else:
                        time.sleep(0.1)
                    end = time.perf_counter()
                    if end - start > 1.0:
                        break

            else:
                # print("BgThread recv...")
                if channel.recv_ready():
                    # fp.write(channel.recv(65535))
                    buf = channel.recv(65535)
                    if isinstance(fp, io.TextIOBase):
                        fp.write(buf.decode())
                    else:
                        fp.write(buf)
                else:
                    # Wait if no data are ready on the channel yet
                    time.sleep(0.01)

        # print("end of bgthread")

    def wait(self):
        done = False
        while not done:
            if self.channel.exit_status_ready() or self.channel.eof_received:
                done = True


class SshServer:
    def __init__(self, server_opts: ServerOpts):
        self.opts: ServerOpts = server_opts
        self.client = paramiko.client.SSHClient()
        # TODO: security warning? is this relevant here?
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(
            self.opts.ssh_host, self.opts.ssh_port, username=self.opts.ssh_user, password=self.opts.ssh_pwd
        )
        # TODO: rename to sftp_client
        self.ftp_client: SFTPClient = self.client.open_sftp()

    def send_file(self, src: Path, dst: Path, file_permission: bool):
        # TODO: put() has a confirm parameter? use it?
        self.ftp_client.put(str(src), str(dst))
        if file_permission:
            # try to copy file permission
            self.ftp_client.chmod(str(dst), Path(src).stat().st_mode)

    def mkdir(self, folder: Path, exist_ok: bool = False, parents: bool = False):
        # TODO: document behavior if folder already exists? parents?
        # print("Trying to create folder", folder)
        if exist_ok:
            # TODO: use exception provided by mkdir instead of doing this
            #       EAFP: Easier to Ask Forgiveness than Permission
            try:
                with self.ftp_client.open(str(folder), "r"):
                    pass
            except FileNotFoundError:
                self.ftp_client.mkdir(str(folder))
        else:
            self.ftp_client.mkdir(str(folder))

    def mkdtemp(self, prefix: Optional[str]):
        now = datetime.datetime.now()
        suffix = now.strftime("%Y%m%d_%H%M%S_%f")
        tmp_folder = prefix or "tmp_py_mf_"
        tmp_folder = Path("/tmp") / (tmp_folder + suffix)
        # TODO: if it fails, can wait a bit randomly and retry?
        # print("Try to create remotly", tmp_folder)
        self.mkdir(str(tmp_folder))
        return tmp_folder

    def open(self, path: str, mode: str) -> SFTPFile:
        return self.ftp_client.open(path, mode)

    def remove(self, path: str) -> None:
        return self.ftp_client.remove(path)

    def run(
        self,
        cmd: List[str],
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        stdout=sys.stdout,
        stderr=sys.stderr,
    ):
        cmd = cmd[0]

        if env:
            # Note: Channel.set_environment_variable is most of the time restricted so not used here
            cmd_prefix = []
            for env_var, env_value in env.items():
                cmd_prefix.append(f"{env_var}='{env_value}'")
            cmd = " ".join(cmd_prefix) + " " + cmd

        if cwd:
            # Emulate cwd
            cmd = f"cd {cwd} && " + cmd
        transport = self.client.get_transport()
        proc = ParamikoRemotePopen(transport.open_session())
        print("[SshServer] Run", cmd, "- env:", env)
        return proc.run(cmd, stdout=stdout)
        # return proc


class Server:
    def __init__(self, server_opts: ServerOpts):
        self.server_opts = server_opts

        if server_opts.local:
            self.server = None
        else:
            self.server = SshServer(server_opts)

        self._cleanup = []

    def send_file(self, src: Path, dst: Path, file_permission: bool = True):
        if self.server_opts.local:
            shutil.copy(src, dst)
        else:
            self.server.send_file(src, dst, file_permission)

    def run(
        self,
        cmd: List[str],
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        stdout=sys.stdout,
        stderr=sys.stderr,
    ):
        if self.server_opts.local:
            return subprocess.Popen(
                cmd, cwd=cwd, shell=True, env=env, stdout=stdout, stderr=stderr
            )
            # TODO: git clone with shell=True fails but why?
            # return subprocess.Popen(cmd, cwd=cwd)
        else:
            # TODO: handle stdout & stderr
            return self.server.run(cmd, cwd, env=env, stdout=stdout, stderr=stderr)

    def mkdtemp(self, prefix: Optional[str]) -> Path | RemotePath:
        if self.server_opts.local:
            p = Path(tempfile.mkdtemp(prefix=prefix))
        else:
            p = RemotePath(self.server.mkdtemp(prefix=prefix), server=self)

        self._cleanup.append(p)
        return p

    def mkdir(self, folder: Path):
        if self.server_opts.local:
            folder.mkdir(parents=True, exist_ok=True)
        else:
            self.server.mkdir(folder, exist_ok=True)

    def open(self, path: str, mode: str):
        if self.server_opts.local:
            return open(path, mode=mode)
        else:
            return self.server.open(str(path), mode)

    def remove(self, path: str) -> None:
        if self.server_opts.local:
            return os.unlink(path)
        else:
            return self.server.remove(str(path))

    def stop(self, process):
        if self.server_opts.local:
            process.terminate()

    @property
    def host(self) -> str:
        """Server host (e.g. ip) as string"""
        if self.server_opts.local:
            return "127.0.0.1"
        else:
            return self.server_opts.ssh_host
