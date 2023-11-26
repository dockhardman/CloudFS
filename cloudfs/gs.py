import base64
import fnmatch
import io
import json
import os
import warnings
from pathlib import Path as _Path
from typing import Dict, Generator, Optional, Set, Text, Union

from yarl import URL

from cloudfs.base import Path

try:
    from google.auth.credentials import Credentials
    from google.cloud.storage.blob import Blob
    from google.cloud.storage.bucket import Bucket
    from google.cloud.storage.client import Client
    from google.oauth2 import service_account

    service_account
except ImportError:
    warnings.warn(
        "Required 'google-cloud-storage' is not installed, "
        "please install it with 'pip install google-cloud-storage'"
    )
    storage = None

EMPTY_FILENAME = "__empty__"


class GSPath(Path):
    def __init__(
        self,
        path: Union[Text, URL],
        *,
        storage_client: Optional["Client"] = None,
        credentials: Optional[Union["Credentials", Text, Dict]] = None,
        credentials_path: Optional[Union[Text, _Path]] = None,
        empty_filename: Text = EMPTY_FILENAME,
        **kwargs,
    ):
        super().__init__(path, **kwargs)

        if self._url.scheme != "gs":
            raise ValueError(f"Unsupported scheme: gs, got {self._url.scheme}")
        if not self.bucket_name:
            raise ValueError(f"Missing bucket name in {self._url}")

        self._storage_client = self._init_client(
            storage_client=storage_client,
            credentials=credentials,
            credentials_path=credentials_path,
            **kwargs,
        )

        self.empty_filename = empty_filename

    @property
    def client(self) -> "Client":
        return self._storage_client

    @property
    def bucket(self) -> "Bucket":
        return self._storage_client.bucket(self.bucket_name)

    @property
    def bucket_name(self) -> Text:
        return self._url.host

    @property
    def blob(self) -> "Blob":
        return self.bucket.blob(self.blob_name)

    @property
    def blob_name(self) -> Text:
        return self._url.path.lstrip("/")

    def __eq__(self, other_path: "GSPath") -> bool:
        if not isinstance(other_path, GSPath):
            return False
        return self._url == other_path._url

    def __truediv__(self, name: Text) -> "Path":
        if not isinstance(name, Text):
            raise ValueError(f"Expected str, got {type(name)}")
        return GSPath(self._url / name, storage_client=self.client)

    def ping(self) -> bool:
        return self.bucket.exists()

    def samefile(self, other_path: Union[Text, "GSPath"]) -> bool:
        if isinstance(other_path, Text):
            other_path = GSPath(other_path, storage_client=self.client)
        if not isinstance(other_path, GSPath):
            return False
        return self.md5() == other_path.md5()

    def glob(
        self,
        pattern: Text,
        *,
        return_file: bool = True,
        return_dir: bool = True,
        **kwargs,
    ) -> Generator["GSPath", None, None]:
        pattern = "/" + (
            pattern.strip()
            .lstrip(f"{self._url.scheme}://{self.bucket_name}")
            .lstrip("/")
        )
        prefix = pattern.split("*")[0]
        blobs = self.client.list_blobs(self.bucket_name, prefix=prefix, delimiter="/")

        paths: Set[Text] = set()

        for page in blobs.pages:
            if page.prefixes and return_dir:
                matched_dirs = {d for d in page.prefixes if fnmatch.fnmatch(d, pattern)}
                for matched_dir in matched_dirs:
                    if matched_dir in paths:
                        continue
                    paths.add(matched_dir)
                    yield GSPath(
                        self._url.with_path(matched_dir.strip(" /") + "/"),
                        storage_client=self.client,
                    )
            for blob in page:
                if return_file and fnmatch.fnmatch(blob.name, pattern):
                    if blob.name in paths:
                        continue
                    paths.add(blob.name)
                    yield GSPath(
                        self._url.with_path(matched_dir.strip(" /") + "/"),
                        storage_client=self.client,
                    )

    def stat(self) -> Dict[Text, Union[int, float]]:
        blob = self.blob
        blob.reload(client=self.client)
        return {
            "size": blob.size,
            "mtime": blob.updated.timestamp(),
            "ctime": blob.time_created.timestamp(),
        }

    def owner(self) -> Text:
        blob = self.blob
        blob.reload(client=self.client)
        return blob.owner

    def group(self) -> Text:
        blob = self.blob
        blob.reload(client=self.client)
        return blob.owner

    def open(self, **kwargs) -> io.IOBase:
        raise NotImplementedError

    def read_bytes(self) -> bytes:
        return self.blob.download_as_bytes(client=self.client)

    def read_text(self, encoding=None, errors=None) -> Text:
        return self.blob.download_as_text(client=self.client)

    def write_bytes(self, data: bytes) -> int:
        self.blob.upload_from_string(data, client=self.client)
        return len(data)

    def write_text(self, data, encoding=None, errors=None) -> int:
        self.blob.upload_from_string(data, client=self.client)
        return len(data)

    def touch(self, mode=None, exist_ok=True) -> None:
        if self._url.path.endswith("/"):
            raise IsADirectoryError(f"Is a directory: {self}")
        if self.is_file():
            if not exist_ok:
                raise FileExistsError(f"File already exists: {self}")
            return
        else:
            self.blob.upload_from_string(b"", client=self.client)

    def mkdir(self, mode=None, parents: bool = False, exist_ok: bool = False) -> None:
        if not self._url.path.endswith("/"):
            path = GSPath(
                self._url.with_path(self._url.path + "/"), storage_client=self.client
            )
        else:
            path = self

        if path.is_dir():
            if not exist_ok:
                raise FileExistsError(f"Directory already exists: {path}")
            return
        else:
            (path / self.empty_filename).touch()

    def unlink(self, missing_ok=False) -> None:
        blob = self.blob
        try:
            blob.reload(client=self.client)
        except Exception:
            if missing_ok:
                return
            raise FileNotFoundError(f"No such file or directory: {self}")
        if blob.name.endswith("/"):
            raise IsADirectoryError(f"Is a directory: {self}")
        self.blob.delete(client=self.client)

    def rmdir(self) -> None:
        path = self
        if not path.is_dir():
            raise FileNotFoundError(f"No such file or directory: {self}")

        path_empty: Optional["GSPath"] = None
        for inner_path in path.glob(
            path._url.path + "*", return_file=True, return_dir=True
        ):
            if inner_path._url.name == path.empty_filename:
                path_empty = inner_path
                continue
            raise OSError(f"Directory not empty: {self}")

        if path_empty:
            path_empty.unlink()

    def rename(self, target) -> "Path":
        raise NotImplementedError

    def replace(self, target) -> "Path":
        raise NotImplementedError

    def exists(self) -> bool:
        if self._url.path.endswith("/"):
            return self.is_dir()
        return self.is_file()

    def is_dir(self) -> bool:
        if (self / self.empty_filename).is_file():
            return True
        pattern = self._url.path
        if not pattern.endswith("/"):
            pattern += "/"
        pattern += "*"
        for _ in self.glob(pattern, return_file=True, return_dir=True):
            return True
        return False

    def is_file(self) -> bool:
        if self._url.path.endswith("/"):
            return False
        return self.blob.exists(client=self.client)

    def md5(self) -> Text:
        blob = self.blob
        blob.reload(client=self._storage_client)
        md5_hash_base64 = blob.md5_hash
        return base64.b64decode(md5_hash_base64).hex()

    def _init_client(
        self,
        storage_client: Optional["Client"] = None,
        credentials: Optional[Union["Credentials", Text, Dict]] = None,
        credentials_path: Optional[Union[Text, _Path]] = None,
        **kwargs,
    ) -> "Client":
        if isinstance(storage_client, Client):
            return storage_client

        if isinstance(credentials, Text):
            credentials = service_account.Credentials.from_service_account_info(
                json.loads(credentials)
            )
        elif isinstance(credentials, Dict):
            credentials = service_account.Credentials.from_service_account_info(
                credentials
            )
        elif not credentials and credentials_path:
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path
            )
        elif not credentials and "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
            if os.environ["GOOGLE_APPLICATION_CREDENTIALS"].endswith(".json"):
                credentials = service_account.Credentials.from_service_account_file(
                    os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
                )
            else:
                credentials = service_account.Credentials.from_service_account_info(
                    json.loads(os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
                )

        return Client(credentials=credentials)
