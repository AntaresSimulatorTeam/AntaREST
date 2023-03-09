import sys
import time
from datetime import datetime, timedelta, timezone
from functools import wraps
from pathlib import Path
from typing import Any, Callable
from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine

from antarest.core.model import SUB_JSON
from antarest.core.utils.fastapi_sqlalchemy import DBSessionMiddleware, db
from antarest.dbmodel import Base

project_dir: Path = Path(__file__).parent.parent
sys.path.insert(0, str(project_dir))


@pytest.fixture
def project_path() -> Path:
    return project_dir


def with_db_context(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        engine = create_engine("sqlite:///:memory:", echo=True)
        Base.metadata.create_all(engine)
        # noinspection PyTypeChecker
        DBSessionMiddleware(
            Mock(),
            custom_engine=engine,
            session_args={"autocommit": False, "autoflush": False},
        )
        with db():
            return f(*args, **kwargs)

    return wrapper


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


def auto_retry_assert(
    predicate: Callable[..., bool], timeout: int = 2
) -> None:
    threshold = datetime.now(timezone.utc) + timedelta(seconds=timeout)
    while datetime.now(timezone.utc) < threshold:
        if predicate():
            return
        time.sleep(0.2)
    raise AssertionError()
