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
    from google.cloud import storage
    from google.cloud.storage.blob import Blob
    from google.cloud.storage.bucket import Bucket
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
        credentials: Optional[Union["Credentials", Text, Dict]] = None,
        credentials_path: Optional[Union[Text, _Path]] = None,
        **kwargs,
    ):
        super().__init__(path, **kwargs)

        if self._url.scheme != "gs":
            raise ValueError(f"Unsupported scheme: gs, got {self._url.scheme}")
        if not self.bucket_name:
            raise ValueError(f"Missing bucket name in {self._url}")

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

        self._storage_client = storage.Client(credentials=credentials)

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

    def __eq__(self, other_path: "Path") -> bool:
        raise NotImplementedError

    def __truediv__(self, name: Text) -> "Path":
        raise NotImplementedError

    def ping(self) -> bool:
        return self.bucket.exists()

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
