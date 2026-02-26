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

from pydantic import validate_call

from antarest.core.api_types import SanitizedStr


def to_pascal_case(value: str) -> str:
    return "".join(word.capitalize() for word in value.split("_"))


def to_camel_case(value: str) -> str:
    v = to_pascal_case(value)
    return v[0].lower() + v[1:] if len(v) > 0 else ""


def to_kebab_case(string: str) -> str:
    return string.replace("_", "-")


@validate_call
def check_sanitized(string: SanitizedStr) -> SanitizedStr:
    """
    Raises if the string contains newline characters, and should therefore not be logged, in particular.

    See sonar issue python:5145
    """
    return string
