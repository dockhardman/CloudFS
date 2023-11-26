import os
from datetime import datetime

import pytest

from cloudfs import Path
from cloudfs.gs import GSPath

test_dirname = f"test-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"


@pytest.fixture(scope="module")
def test_dir():
    test_bucket_name = os.environ.get("TEST_GS_BUCKET_NAME", "cloudfs-test")
    url = f"gs://{test_bucket_name}/{test_dirname}"
    test_path = Path(url)
    yield test_path
    # test_path.rmdir()


def test_gs_path_basic_operations(test_dir: "GSPath"):
    # test client and bucket
    assert test_dir.ping()

    # Initiation
    test_dir.mkdir(exist_ok=True)
