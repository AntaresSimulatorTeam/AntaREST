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
Contains various utilities for pydantic models validation.
"""

from typing import Annotated, Any, Dict, List, TypeAlias

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
ItemName: TypeAlias = Annotated[str, BeforeValidator(_validate_item_name)]

# Type to be used for area identifiers. An ID is valid if it contains
# only lower case alphanumeric characters, parenthesis, comma,
# ampersand, spaces, underscores, or dashes, as defined by
# antares-simulator.
AreaId: TypeAlias = Annotated[str, Field(description="Area ID", pattern=r"^[a-z0-9_(),& -]+$")]


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
