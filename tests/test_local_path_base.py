import shutil
from typing import TYPE_CHECKING

import pytest

from cloudfs.base import LocalPath

if TYPE_CHECKING:
    from _pytest.tmpdir import TempPathFactory


@pytest.fixture(scope="module")
def temp_dir(tmp_path_factory: "TempPathFactory"):
    temp_dir = tmp_path_factory.mktemp("data")
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_local_path_basic_operations(temp_dir):
    pass
