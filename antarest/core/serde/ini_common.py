# Copyright (c) 2025, RTE (https://www.rte-france.com)
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

import dataclasses
from typing import Optional, TypeAlias

PrimitiveType: TypeAlias = str | int | float | bool


@dataclasses.dataclass(frozen=True)
class OptionMatcher:
    """
    Used to match a location in an INI file:
    a None section means any section.
    """

    section: Optional[str]
    key: str


def any_section_option_matcher(key: str) -> OptionMatcher:
    """
    Return a matcher which will match the provided key in any section.
    """
    return OptionMatcher(section=None, key=key)
