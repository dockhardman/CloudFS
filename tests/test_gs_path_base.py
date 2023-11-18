import os
from datetime import datetime

from cloudfs import Path


def test_gs_path_basic_operations():
    test_bucket_name = os.environ.get("TEST_GS_BUCKET_NAME", "cloudfs-test")
    test_dirname = f"test-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
    url = f"gs://{test_bucket_name}"
    path = Path(url)

    # test client and bucket
    assert path.ping()
