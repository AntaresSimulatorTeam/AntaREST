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
from typing import Callable, Iterable, TypeVar

from antarest.core.utils.typing_utils import Predicate

T = TypeVar("T")
U = TypeVar("U")


def find_if(iterable: Iterable[T], predicate: Predicate[T]) -> T | None:
    """
    Returns the first element matching the predicate, or None.
    """
    return next(filter(predicate, iterable), None)


def find_first(iterable: Iterable[T], func: Callable[[T], U]) -> U | None:
    """
    Returns the first not-None element when applying func to iterable.
    """
    results = map(func, iterable)
    return find_if(results, lambda x: x is not None)
