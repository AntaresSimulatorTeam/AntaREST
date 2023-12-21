import os
import tempfile

from antarest.study.service import get_disk_usage


def test_get_disk_usage():
    test_study_id = "1edf11fe-cc77-40d3-980a-20790137cfb7"
    test_dir = os.path.join(tempfile.gettempdir(), test_study_id)
    os.makedirs(test_dir, exist_ok=True)
    assert get_disk_usage(test_dir) == 0
