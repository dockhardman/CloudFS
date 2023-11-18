from cloudfs.base import LocalPath, Path
from cloudfs.gs import GSPath


def test_path_initiation():
    assert type(Path("file:///home/user/file.bz2")) == LocalPath
    assert type(Path(path="file:///home/user/file.bz2")) == LocalPath
    assert type(Path("gs://bucket/path/to/file")) == GSPath
