# Copyright (c) 2026, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import hashlib
import math
import os
import time
import uuid
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from functools import wraps
from pathlib import Path
from typing import Any, cast
from unittest.mock import Mock

import numpy as np
import polars as pl
from numpy import typing as npt
from polars.testing import assert_frame_equal
from typing_extensions import override

from antarest.core.model import SUB_JSON
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.login.utils import current_user_context
from antarest.study.business.study_interface import FileStudyInterface
from antarest.study.model import RawStudy, Study
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy
from tests.conftest_instances import create_admin_user


def dirhash(dirname: str | Path, hashfunc: str = "md5") -> str:
    """Compute a single hash for all files in a directory tree (replacement for checksumdir.dirhash)."""
    hash_constructor = getattr(hashlib, hashfunc)
    hashvalues = []
    for root, dirs, files in os.walk(str(dirname)):
        dirs.sort()
        files.sort()
        for fname in files:
            hasher = hash_constructor()
            filepath = os.path.join(root, fname)
            with open(filepath, "rb") as fp:
                for chunk in iter(lambda: fp.read(65536), b""):
                    hasher.update(chunk)
            hashvalues.append(hasher.hexdigest())
    hasher = hash_constructor()
    for h in sorted(hashvalues):
        hasher.update(h.encode("utf-8"))
    return hasher.hexdigest()


def with_db_context(f: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        with db():
            return f(*args, **kwargs)

    return wrapper


def with_admin_user(f: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        user = create_admin_user()
        with current_user_context(user):
            return f(*args, **kwargs)

    return wrapper


def _assert_dict(a: dict[str, Any], b: dict[str, Any]) -> None:
    if a.keys() != b.keys():
        raise AssertionError(f"study level has not the same keys {a.keys()} != {b.keys()}")
    for k, v in a.items():
        assert_study(v, b[k])


def _assert_list(a: list[Any], b: list[Any]) -> None:
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


def _assert_array(
    a: npt.NDArray[np.float64],
    b: npt.NDArray[np.float64],
) -> None:
    # noinspection PyUnresolvedReferences
    if not (a == b).all():
        raise AssertionError(f"element in study not the same {a} != {b}")


def assert_study(a: SUB_JSON, b: SUB_JSON) -> None:
    if isinstance(a, pl.DataFrame) and isinstance(b, pl.DataFrame):
        assert_frame_equal(a, b, check_dtypes=False)
    elif isinstance(a, dict) and isinstance(b, dict):
        _assert_dict(a, b)
    elif isinstance(a, list) and isinstance(b, list):
        _assert_list(a, b)
    elif isinstance(a, str) and isinstance(b, str) and "studyfile://" in a and "studyfile://" in b:
        _assert_pointer_path(a, b)
    elif isinstance(a, np.ndarray) and isinstance(b, np.ndarray):
        _assert_array(a, b)
    elif isinstance(a, np.ndarray) and isinstance(b, list):
        _assert_list(cast(list[float], a.tolist()), b)
    elif isinstance(a, list) and isinstance(b, np.ndarray):
        _assert_list(a, cast(list[float], b.tolist()))
    elif isinstance(a, float) and math.isnan(a):
        assert math.isnan(b)
    else:
        _assert_others(a, b)


def auto_retry_assert(predicate: Callable[..., bool], timeout: int = 2, delay: float = 0.2) -> None:
    threshold = datetime.now(timezone.utc) + timedelta(seconds=timeout)
    while datetime.now(timezone.utc) < threshold:
        if predicate():
            return
        time.sleep(delay)
    raise AssertionError()


class AnyUUID:
    """Mock object to match any UUID."""

    def __init__(self, as_string: bool = False):
        self.as_string = as_string

    @override
    def __eq__(self, other: object) -> bool:
        if isinstance(other, AnyUUID):
            return True
        if isinstance(other, str):
            if self.as_string:
                try:
                    uuid.UUID(other)
                    return True
                except ValueError:
                    return False
            return False
        return isinstance(other, uuid.UUID)

    @override
    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)


def create_study(
    id: str | None = None,
    name: str | None = None,
    path: str | None = None,
    version: str = "880",
    **kwargs: Any,
) -> Study:
    """
    Factory to create a new Study object for testing purposes.

    Args:
        id: The study ID. If not provided, a new UUID is generated.
        name: The study name. If not provided, it will be "My Study".
        path: The study path. If not provided, a temporary path is created.
        version: The study version. Default is "860".
        **kwargs: Additional keyword arguments to pass to the Study constructor.

    Returns:
        A new Study object.
    """
    return Study(
        id=id or str(uuid.uuid4()),
        name=name or "My Study",
        path=str(path or Path("path/to/study")),
        version=version,
        **kwargs,
    )


def create_raw_study(
    id: str | None = None,
    name: str | None = None,
    path: str | None = None,
    version: str = "880",
    **kwargs: Any,
) -> RawStudy:
    """
    Factory to create a new RawStudy object for testing purposes.

    Args:
        id: The study ID. If not provided, a new UUID is generated.
        name: The study name. If not provided, it will be "My Study".
        path: The study path. If not provided, a temporary path is created.
        version: The study version. Default is "860".
        **kwargs: Additional keyword arguments to pass to the RawStudy constructor.

    Returns:
        A new RawStudy object.
    """
    return RawStudy(
        id=id or str(uuid.uuid4()),
        name=name or "My Study",
        path=str(path or Path("path/to/raw_study")),
        version=version,
        **kwargs,
    )


def create_variant_study(
    id: str | None = None,
    name: str | None = None,
    path: str | None = None,
    version: str = "880",
    **kwargs: Any,
) -> VariantStudy:
    """
    Factory to create a new VariantStudy object for testing purposes.

    Args:
        id: The study ID. If not provided, a new UUID is generated.
        name: The study name. If not provided, it will be "My Study".
        path: The study path. If not provided, a temporary path is created.
        version: The study version. Default is "860".
        **kwargs: Additional keyword arguments to pass to the VariantStudy constructor.

    Returns:
        A new VariantStudy object.
    """
    return VariantStudy(
        id=id or str(uuid.uuid4()),
        name=name or "My Study",
        path=str(path or Path("path/to/variant_study")),
        version=version,
        **kwargs,
    )


def file_study_interface(file_study: FileStudy) -> FileStudyInterface:
    """
    Utils function to avoid declaring Mocks everywhere inside the tests
    """
    return FileStudyInterface(file_study, Mock(), Mock())
