import sys
from pathlib import Path
from typing import Any

import pytest

from antarest.core.model import SUB_JSON

project_dir: Path = Path(__file__).parent.parent
sys.path.insert(0, str(project_dir))


@pytest.fixture
def project_path() -> Path:
    return project_dir


def _assert_dict(a: dict, b: dict) -> None:
    if a.keys() != b.keys():
        raise AssertionError(
            f"study level has not the same keys {a.keys()} != {b.keys()}"
        )
    for k, v in a.items():
        assert_study(v, b[k])


def _assert_list(a: list, b: list) -> None:
    for i, j in zip(a, b):
        assert_study(i, j)


def _assert_pointer_path(a: str, b: str) -> None:
    # pointer is like studyfile://study-id/a/b/c
    # we should compare a/b/c only
    if a.split("/")[4:] != b.split("/")[4:]:
        raise AssertionError(f"element in study not the same {a} != {b}")


def _assert_others(a: Any, b: Any) -> None:
    if a != b:
        raise AssertionError(f"element in study not the same {a} != {b}")


def assert_study(a: SUB_JSON, b: SUB_JSON) -> None:
    if isinstance(a, dict) and isinstance(b, dict):
        _assert_dict(a, b)
    elif isinstance(a, list) and isinstance(b, list):
        _assert_list(a, b)
    elif (
        isinstance(a, str)
        and isinstance(b, str)
        and "studyfile://" in a
        and "studyfile://" in b
    ):
        _assert_pointer_path(a, b)
    else:
        _assert_others(a, b)
