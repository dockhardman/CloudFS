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

    # test create file
    filename = "test_create_file"
    filepath = path / filename
    filepath.touch()
    assert filepath.exists()
    assert filepath.is_file()

    # test create directory
    dirname = "test_create_dir"
    dirpath = path / dirname
    dirpath.mkdir()
    assert dirpath.exists()
    assert dirpath.is_dir()

    # test file stat
    filename = "test_stat"
    filepath = path / filename
    filepath.touch()
    assert filepath.stat()
    assert filepath.owner()
    assert filepath.group()
    dirname = "test_stat_dir"
    dirpath = path / dirname
    dirpath.mkdir()
    assert dirpath.stat()
    assert dirpath.owner()
    assert dirpath.group()

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

    # test remove file and directory
    filename = "test_remove"
    filepath = path / filename
    filepath.touch()
    assert filepath.exists()
    filepath.unlink()
    assert not filepath.exists()
    dirname = "test_remove_dir"
    dirpath = path / dirname
    dirpath.mkdir()
    assert dirpath.exists()
    dirpath.rmdir()
    assert not dirpath.exists()

    # test rename and replace
    filename = "test_rename"
    filepath = path / filename
    filepath.touch()
    assert filepath.exists()
    new_filename = "test_rename_new"
    new_filepath = path / new_filename
    assert new_filepath == filepath.rename(new_filepath)
    assert not filepath.exists()
    assert new_filepath.exists()
    new_filepath.unlink()
    filename = "test_replace"
    filepath = path / filename
    filepath.touch()
    assert filepath.exists()
    new_filename = "test_replace_new"
    new_filepath = path / new_filename
    assert new_filepath == filepath.replace(new_filepath)
    assert not filepath.exists()
    assert new_filepath.exists()
