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
    assert path.samefile(LocalPath(temp_dir.as_uri()))
    assert not path.samefile(LocalPath("file:///tmp"))

    # test write_bytes and read_bytes
    bytes_filename = "test_bytes"
    data = b"test"
    bytes_filepath = path / bytes_filename
    assert bytes_filepath.write_bytes(data)
    assert bytes_filepath.read_bytes() == data

    # test write_text and read_text
    text_filename = "test_text"
    data = "test"
    text_filepath = path / text_filename
    assert text_filepath.write_text(data)
    assert text_filepath.read_text() == data
