import base64
import io
import json
import os
import warnings
from pathlib import Path as _Path
from typing import Dict, Generator, Optional, Text, Union

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


class GSPath(Path):
    def __init__(
        self,
        path: Union[Text, URL],
        *,
        storage_client: Optional["Client"] = None,
        credentials: Optional[Union["Credentials", Text, Dict]] = None,
        credentials_path: Optional[Union[Text, _Path]] = None,
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
        return GSPath(self._url / name, storage_client=self._storage_client)

    def ping(self) -> bool:
        return self.bucket.exists()

    def samefile(self, other_path: Union[Text, "GSPath"]) -> bool:
        if isinstance(other_path, Text):
            other_path = GSPath(other_path, storage_client=self._storage_client)
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
