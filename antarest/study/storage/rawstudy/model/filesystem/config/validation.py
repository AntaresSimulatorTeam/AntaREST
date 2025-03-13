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

"""
Contains various utilities for pydantic models validation.
"""

from typing import Annotated, Any, Dict, List, Mapping, MutableMapping

from antares.study.version import StudyVersion
from pydantic import BeforeValidator, Field
from pydantic_core.core_schema import ValidationInfo

from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id

_ALL_FILTERING = ["hourly", "daily", "weekly", "monthly", "annual"]


def _validate_item_name(name: Any) -> str:
    if isinstance(name, int):
        name = str(name)
    if not isinstance(name, str):
        raise ValueError(f"Invalid name '{name}'.")
    if not transform_name_to_id(name):
        raise ValueError(f"Invalid name '{name}'.")
    return name


# Type to be used for item names, will raise an error if name
# does not comply with antares-simulator limitations.
ItemName = Annotated[str, BeforeValidator(_validate_item_name)]

# Type to be used for area identifiers. An ID is valid if it contains
# only lower case alphanumeric characters, parenthesis, comma,
# ampersand, spaces, underscores, or dashes, as defined by
# antares-simulator.
AreaId = Annotated[str, Field(description="Area ID", pattern=r"^[a-z0-9_(),& -]+$")]


def extract_filtering(v: Any) -> List[str]:
    """
    Extract filtering values from a comma-separated list of values.
    """

    if v is None:
        values = set()
    elif isinstance(v, str):
        values = {x.strip() for x in v.lower().split(",")} if v else set()
    elif isinstance(v, (list, tuple)):
        values = set(x.strip().lower() for x in v)
    else:
        raise TypeError(f"Invalid type for filtering: {type(v)!r}")

    try:
        return sorted(values, key=lambda x: _ALL_FILTERING.index(x))
    except ValueError as e:
        raise ValueError(f"Invalid value for filtering: {e!s}") from None


def validate_filtering(v: Any) -> str:
    """
    Validate the filtering field and convert it to a comma separated string.
    """

    return ", ".join(extract_filtering(v))


# noinspection SpellCheckingInspection
def validate_colors(values: MutableMapping[str, Any]) -> Mapping[str, Any]:
    """
    Validate ``color_rgb``, ``color_r``, ``color_g``, ``color_b`` and convert them to ``color_rgb``.
    """

    def _pop_any(dictionary: MutableMapping[str, Any], *keys: str) -> Any:
        """Save as `pop` but for multiple keys. Return the first found value."""
        return next((dictionary.pop(key, None) for key in keys if key in dictionary), None)

    color_r = _pop_any(values, "color_r", "colorr")
    color_g = _pop_any(values, "color_g", "colorg")
    color_b = _pop_any(values, "color_b", "colorb")
    if color_r is not None and color_g is not None and color_b is not None:
        values["color_rgb"] = color_r, color_g, color_b
    return values


def validate_color_rgb(v: Any) -> str:
    """
    Validate RGB color field and convert it to color code.

    Accepts:
        - a string in the format "#RRGGBB"
        - a string in the format "rgb(R, G, B)"
        - a string in the format "R, G, B"
        - a list or tuple of 3 integers
    """

    if isinstance(v, str):
        if v.startswith("#"):
            r = int(v[1:3], 16)
            g = int(v[3:5], 16)
            b = int(v[5:7], 16)
        elif v.startswith("rgb("):
            r, g, b = [int(c) for c in v[4:-1].split(",")]
        else:
            r, g, b = [int(c) for c in v.split(",")]
    elif isinstance(v, (list, tuple)):
        r, g, b = map(int, v)
    else:
        raise TypeError(f"Invalid type for 'color_rgb': {type(v)}")

    return f"#{r:02X}{g:02X}{b:02X}"


STUDY_VERSION_KEY: str = "study_version"


def study_version_context(study_version: StudyVersion) -> Dict[str, Any]:
    """
    Creates a context for pydantic validation, containing this study version.
    """
    return {STUDY_VERSION_KEY: study_version}


def extract_version(info: ValidationInfo) -> StudyVersion:
    """
    Extract study version from pydantic validation context.
    """
    if info.context:
        if study_version := info.context.get(STUDY_VERSION_KEY, None):
            if isinstance(study_version, StudyVersion):
                return study_version
    raise ValueError("You must provide a study version to validate this model.")
