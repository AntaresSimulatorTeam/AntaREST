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
from collections.abc import Iterable
from itertools import groupby
from typing import Callable, Iterable, TypeVar

from antarest.output.storage.v2.variables_metadata import T, V

T = TypeVar("T")
U = TypeVar("U")
V = TypeVar("V")
W = TypeVar("W")
X = TypeVar("X")


K = TypeVar("K")
K1 = TypeVar("K1")
K2 = TypeVar("K2")


def remove_nones(data: dict[T, V]) -> dict[T, V]:
    return dict(filter(lambda x: x[1] is not None, data.items()))


def iter_nested(data: dict[T, dict[U, V]]) -> Iterable[tuple[T, U, V]]:
    """
    Allows to flatten iterations on a nested dictionary.
    """
    for k1, v1 in data.items():
        for k2, v2 in v1.items():
            yield k1, k2, v2


def iter_nested_2(data: dict[T, dict[U, dict[V, W]]]) -> Iterable[tuple[T, U, V, W]]:
    """
    Allows to flatten iterations on a double-nested dictionary.
    """
    for k1, v1 in data.items():
        for k2, v2 in v1.items():
            for k3, v3 in v2.items():
                yield k1, k2, k3, v3


def iter_nested_3(data: dict[T, dict[U, dict[V, dict[W, X]]]]) -> Iterable[tuple[T, U, V, W, X]]:
    """
    Allows to flatten iterations on a triple-nested dictionary.
    """
    for k1, v1 in data.items():
        for k2, v2 in v1.items():
            for k3, v3 in v2.items():
                for k4, v4 in v3.items():
                    yield k1, k2, k3, k4, v4


def _group_by(data: Iterable[T], key: Callable[[T], K], value: Callable[[T], V]) -> dict[K, list[V]]:
    res = {}
    for k, items in groupby(data, key=key):
        res[k] = [value(i) for i in items]
    return res


def _group_by_2(
    data: Iterable[T], key1: Callable[[T], K1], key2: Callable[[T], K2], value: Callable[[T], V]
) -> dict[K1, dict[K2, list[V]]]:
    res = {}
    for k, items in groupby(data, key=key1):
        res[k] = _group_by(items, key=key2, value=value)
    return res
