import io
from pathlib import Path as _Path
from typing import Dict, Generator, Text, Type, Union

from yarl import URL

support_schemes = ("file", "gs", "s3", "azure")


class Path:
    def __new__(cls: Type["Path"], *args, **kwargs) -> "Path":
        path = args[0] if args else kwargs.get("path")
        if not path:
            raise ValueError("Paramter 'path' is required")
        if cls == Path:
            if str(path).startswith("file://"):
                return object.__new__(LocalPath)
            elif str(path).startswith("gs://"):
                from cloudfs.gs import GSPath

                return object.__new__(GSPath)
            elif str(path).startswith("s3://"):
                from cloudfs.s3 import S3Path

                return object.__new__(S3Path)
            elif str(path).startswith("azure://"):
                from cloudfs.azure import AzurePath

                return object.__new__(AzurePath)
        return object.__new__(cls)

    def __init__(self, path: Union[Text, "URL"], **kwargs):
        self._url = URL(path)

        if self._url.scheme not in support_schemes:
            raise ValueError(
                f"Unsupported scheme: {support_schemes}, got {self._url.scheme}"
            )

    def __str__(self):
        return str(self._url)

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other_path: "Path") -> bool:
        raise NotImplementedError

    def __truediv__(self, name: Text) -> "Path":
        raise NotImplementedError

    def ping(self) -> bool:
        raise NotImplementedError

    def samefile(self, other_path) -> bool:
        raise NotImplementedError

    def glob(
        self,
        pattern: Text,
        *,
        return_file: bool = True,
        return_dir: bool = True,
        **kwargs,
    ) -> Generator["Path", None, None]:
        raise NotImplementedError

    def stat(self) -> Dict[Text, Union[int, float]]:
        raise NotImplementedError

    def owner(self) -> Text:
        raise NotImplementedError

    def group(self) -> Text:
        raise NotImplementedError

    def open(self, **kwargs) -> io.IOBase:
        raise NotImplementedError

    def read_bytes(self) -> bytes:
        raise NotImplementedError

    def read_text(self, encoding=None, errors=None) -> Text:
        raise NotImplementedError

    def write_bytes(self, data) -> int:
        raise NotImplementedError

    def write_text(self, data, encoding=None, errors=None) -> int:
        raise NotImplementedError

    def touch(self, mode=438, exist_ok=True) -> None:
        raise NotImplementedError

    def mkdir(self, mode=511, parents=False, exist_ok=False) -> None:
        raise NotImplementedError

    def unlink(self, missing_ok=False) -> None:
        raise NotImplementedError

    def rmdir(self) -> None:
        raise NotImplementedError

    def rename(self, target) -> "Path":
        raise NotImplementedError

    def replace(self, target) -> "Path":
        raise NotImplementedError

    def exists(self) -> bool:
        raise NotImplementedError

    def is_dir(self) -> bool:
        raise NotImplementedError

    def is_file(self) -> bool:
        raise NotImplementedError


class LocalPath(Path):
    def __init__(self, path: Union[Text, URL], **kwargs):
        super().__init__(path, **kwargs)

    def __eq__(self, other_path: "LocalPath") -> bool:
        if not isinstance(other_path, LocalPath):
            return False
        return self._url == other_path._url

    def __truediv__(self, name: Text) -> "LocalPath":
        if not isinstance(name, Text):
            raise ValueError(f"Expected str, got {type(name)}")
        return LocalPath(self._url / name)

    @property
    def _path(self) -> _Path:
        return _Path((self._url.host or "") + (self._url.path or ""))

    def ping(self) -> bool:
        return True

    def samefile(self, other_path: "LocalPath") -> bool:
        if not isinstance(other_path, LocalPath):
            return False
        other_ = _Path((other_path._url.host or "") + (other_path._url.path or ""))
        return self._path.samefile(other_)

    def glob(
        self,
        pattern: Text,
        *,
        return_file: bool = True,
        return_dir: bool = True,
        **kwargs,
    ) -> Generator["LocalPath", None, None]:
        for i in self._path.glob(pattern):
            if not return_file and i.is_file():
                continue
            if not return_dir and i.is_dir():
                continue
            yield LocalPath(i.as_uri())

    def stat(self) -> Dict[Text, Union[int, float]]:
        stat_info = self._path.stat()
        stat_dict = {
            "st_mode": stat_info.st_mode,
            "st_ino": stat_info.st_ino,
            "st_dev": stat_info.st_dev,
            "st_nlink": stat_info.st_nlink,
            "st_uid": stat_info.st_uid,
            "st_gid": stat_info.st_gid,
            "st_size": stat_info.st_size,
            "st_atime": stat_info.st_atime,
            "st_mtime": stat_info.st_mtime,
            "st_ctime": stat_info.st_ctime,
        }
        return stat_dict

    def owner(self) -> Text:
        return self._path.owner()

    def group(self) -> Text:
        return self._path.group()

    def open(self, **kwargs) -> io.IOBase:
        return self._path.open(**kwargs)

    def read_bytes(self) -> bytes:
        return self._path.read_bytes()

    def read_text(self, encoding=None, errors=None) -> Text:
        return self._path.read_text(encoding=encoding, errors=errors)

    def write_bytes(self, data: bytes) -> int:
        return self._path.write_bytes(data)

    def write_text(self, data, encoding=None, errors=None) -> int:
        return self._path.write_text(data, encoding=encoding, errors=errors)

    def touch(self, mode=438, exist_ok=True) -> None:
        self._path.touch(mode=mode, exist_ok=exist_ok)

    def mkdir(self, mode=511, parents=False, exist_ok=False):
        self._path.mkdir(mode=mode, parents=parents, exist_ok=exist_ok)

    def unlink(self, missing_ok=False) -> None:
        self._path.unlink(missing_ok=missing_ok)

    def rmdir(self) -> None:
        self._path.rmdir()

    def rename(self, target: Union[Text, Path]) -> "LocalPath":
        if not isinstance(target, LocalPath):
            target = LocalPath(target)
        target_path = self._path.rename(target._path)
        return LocalPath(target_path.as_uri())

    def replace(self, target: Union[Text, Path]) -> "LocalPath":
        if not isinstance(target, LocalPath):
            target = LocalPath(target)
        target_path = self._path.replace(target._path)
        return LocalPath(target_path.as_uri())

    def exists(self) -> bool:
        return self._path.exists()

    def is_dir(self) -> bool:
        return self._path.is_dir()

    def is_file(self) -> bool:
        return self._path.is_file()
