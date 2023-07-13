import time
from datetime import datetime, timedelta, timezone
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, cast

import numpy as np
import pytest
from antarest.core.model import SUB_JSON
from antarest.core.utils.fastapi_sqlalchemy import DBSessionMiddleware, db
from antarest.dbmodel import Base
from sqlalchemy import create_engine  # type: ignore

# fmt: off
HERE = Path(__file__).parent.resolve()
PROJECT_DIR = next(iter(p for p in HERE.parents if p.joinpath("antarest").exists()))
# fmt: on


@pytest.fixture
def project_path() -> Path:
    return PROJECT_DIR


def with_db_context(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(engine)
        # noinspection SpellCheckingInspection
        DBSessionMiddleware(
            None,
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


def _assert_array(a: np.ndarray, b: np.ndarray) -> None:
    if not (a == b).all():
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
    elif isinstance(a, np.ndarray) and isinstance(b, np.ndarray):
        _assert_array(a, b)
    elif isinstance(a, np.ndarray) and isinstance(b, list):
        _assert_list(cast(List, a.tolist()), b)
    elif isinstance(a, list) and isinstance(b, np.ndarray):
        _assert_list(a, cast(List, b.tolist()))
    else:
        _assert_others(a, b)


def auto_retry_assert(
    predicate: Callable[..., bool], timeout: int = 2, delay: float = 0.2
) -> None:
    threshold = datetime.now(timezone.utc) + timedelta(seconds=timeout)
    while datetime.now(timezone.utc) < threshold:
        if predicate():
            return
        time.sleep(delay)
    raise AssertionError()
