from pathlib import Path as _Path
from typing import Text, Type, Union

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
                return object.__new__(GSPath)
            elif str(path).startswith("s3://"):
                return object.__new__(S3Path)
            elif str(path).startswith("azure://"):
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

    def samefile(self, other_path) -> bool:
        raise NotImplementedError

    def glob(self, pattern):
        raise NotImplementedError

    def stat(self, *, follow_symlinks=True):
        raise NotImplementedError

    def owner(self):
        raise NotImplementedError

    def group(self):
        raise NotImplementedError

    def open(self, **kwargs):
        raise NotImplementedError

    def read_bytes(self):
        raise NotImplementedError

    def read_text(self, encoding=None, errors=None):
        raise NotImplementedError

    def write_bytes(self, data):
        raise NotImplementedError

    def write_text(self, data, encoding=None, errors=None, newline=None):
        raise NotImplementedError

    def touch(self, mode=0o666, exist_ok=True):
        raise NotImplementedError

    def mkdir(self, mode=0o777, parents=False, exist_ok=False):
        raise NotImplementedError

    def unlink(self, missing_ok=False):
        raise NotImplementedError

    def rmdir(self):
        raise NotImplementedError

    def rename(self, target):
        raise NotImplementedError

    def replace(self, target):
        raise NotImplementedError

    def exists(self):
        raise NotImplementedError

    def is_dir(self):
        raise NotImplementedError

    def is_file(self):
        raise NotImplementedError


class LocalPath(Path):
    def __init__(self, path: Union[Text, URL], **kwargs):
        super().__init__(path, **kwargs)

    def __eq__(self, other_path: "LocalPath") -> bool:
        if not isinstance(other_path, LocalPath):
            return False
        return self._url == other_path._url

    def samefile(self, other_path: "LocalPath") -> bool:
        if not isinstance(other_path, LocalPath):
            return False
        self_ = _Path((self._url.host or "") + (self._url.path or ""))
        other_ = _Path((other_path._url.host or "") + (other_path._url.path or ""))
        return self_.samefile(other_)


class GSPath(Path):
    pass


class S3Path(Path):
    pass


class AzurePath(Path):
    pass
