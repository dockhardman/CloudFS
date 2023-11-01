from cloudfs.base import GSPath, LocalPath, Path


def test_path_initiation():
    assert type(Path("file:///home/user/file.bz2")) == LocalPath
    assert type(Path(path="file:///home/user/file.bz2")) == LocalPath
    assert type(Path("gs://bucket/path/to/file")) == GSPath
