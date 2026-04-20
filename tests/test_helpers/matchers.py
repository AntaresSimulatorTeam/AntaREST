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
"""
Matcher objects to be used in equality assertions for convenience, to check certain conditions on nested objects.

Note: will not respect typing !
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class MatchesCondition(Generic[T]):
    "A helper object to match the end of a path"

    condition: Callable[[T], bool]
    repr: str = "matcher"

    def __eq__(self, other: T) -> bool:
        return self.condition(other)

    def __ne__(self, other: T) -> bool:
        return not self.condition(other)

    def __repr__(self):
        return self.repr


def matches(condition: Callable[[T], bool], repr: str = "matcher") -> MatchesCondition[T]:
    """
    Equals any object which matches the provided condition.
    """
    return MatchesCondition(condition, repr=repr)


def ends_with(suffix: str) -> MatchesCondition[Path]:
    """
    Equals any path which ends with the provided suffix
    """
    return matches(lambda p: p.name.endswith(suffix), repr=f"ends_with({suffix!r})")
