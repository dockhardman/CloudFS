import pathlib
import shutil
from typing import TYPE_CHECKING

import pytest

from cloudfs.base import LocalPath

if TYPE_CHECKING:
    from _pytest.tmpdir import TempPathFactory


@pytest.fixture(scope="module")
def temp_dir(tmp_path_factory: "TempPathFactory"):
    temp_dir = tmp_path_factory.mktemp("test_local_path_base")
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_local_path_basic_operations(temp_dir: "pathlib.PosixPath"):
    # Initiation
    path = LocalPath(temp_dir.as_uri())
    path.mkdir(exist_ok=True)

    # test samefile
    path2 = LocalPath(temp_dir.as_uri())
    assert path.samefile(path2)
    assert not path.samefile(LocalPath("file:///tmp"))
