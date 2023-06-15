import os
import shutil
from pathlib import Path, WindowsPath, PosixPath


class RemotePath(Path):

    _flavour = PosixPath._flavour

    def __new__(cls, *args, **kwargs):

        if "server" not in kwargs:
            raise RuntimeError("Need a server")

        if cls is Path:
            cls = WindowsPath if os.name == 'nt' else PosixPath
        self = cls._from_parts(args)
        if not self._flavour.is_supported:
            raise NotImplementedError("cannot instantiate %r on your system"
                                      % (cls.__name__,))

        self.server = kwargs["server"]
        return self

    def __truediv__(self, other):
        p = super().__truediv__(other)
        p.server = self.server
        return p


def copy_file(src: Path | RemotePath, dst: Path | RemotePath):

    """Copy a file from source (src) to destination (dst)

    This function supports Pathlib.Path & RemotePath on both arguments
    """

    # Note: match order is important here as isinstance(X, Path) returns True even for a RemotePath

    match (src, dst):
        case(src, dst) if isinstance(src, RemotePath) and isinstance(dst, RemotePath):
            # Copy from server to server
            if src.server == dst.server:
                # Copy within the same server
                server = src.server
                with server.open(src, "r") as fp:
                    with server.open(dst, "w+") as fp2:
                        shutil.copyfileobj(fp, fp2)
            else:
                # TODO: try first to copy it from server to server otherwise need to copy locally then send to server?
                raise NotImplementedError
        case(src, dst) if isinstance(src, Path) and isinstance(dst, RemotePath):
            # Upload to server
            # dst.server.mkdir(dst.parents)
            dst.server.send_file(src, dst)
        case(src, dst) if isinstance(src, RemotePath) and isinstance(dst, Path):
            # Download from server
            # Need this one?
            src.server.get_file(src, dst)
        case _:
            # ~ case (src, dst) if isinstance(src, Path) and isinstance(dst, Path):
            # local to local path
            shutil.copy(src, dst)
