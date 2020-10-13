from pathlib import Path

import pytest


@pytest.mark.unit_test
def test_build_child():
    path = Path("parent")
    json_data = {"parent": {}}
    jsm = {}
