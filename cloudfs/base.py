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


class LocalPath(Path):
    pass


class GSPath(Path):
    pass


class S3Path(Path):
    pass


class AzurePath(Path):
    pass
