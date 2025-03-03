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

import re
import typing as t

from pydantic import Field, model_validator

__all__ = ("IgnoreCaseIdentifier", "LowerCaseIdentifier")

from typing_extensions import override

from antarest.core.serde import AntaresBaseModel


class IgnoreCaseIdentifier(
    AntaresBaseModel,
    extra="forbid",
    validate_assignment=True,
    populate_by_name=True,
):
    """
    Base class for all configuration sections with an ID.
    """

    id: str = Field(description="ID (section name)", pattern=r"[a-zA-Z0-9_(),& -]+")

    @classmethod
    def generate_id(cls, name: str) -> str:
        """
        Generate an ID from a name.

        Args:
            name: Name of a section read from an INI file

        Returns:
            The ID of the section.
        """
        # Avoid circular imports

        return transform_name_to_id(name, lower=False)

    @model_validator(mode="before")
    def validate_id(cls, values: t.MutableMapping[str, t.Any]) -> t.Mapping[str, t.Any]:
        """
        Calculate an ID based on the name, if not provided.

        Args:
            values: values used to construct the object.

        Returns:
            The updated values.
        """

        # For some reason I can't explain, values can be an object. If so, no validation is needed.
        if isinstance(values, dict):
            if storage_id := values.get("id"):
                # If the ID is provided, it comes from a INI section name.
                # In some legacy case, the ID was in lower case, so we need to convert it.
                values["id"] = cls.generate_id(storage_id)
                return values
            if not values.get("name"):
                return values
            name = values["name"]
            if storage_id := cls.generate_id(name):
                values["id"] = storage_id
            else:
                raise ValueError(f"Invalid name '{name}'.")
        return values


class LowerCaseIdentifier(IgnoreCaseIdentifier):
    """
    Base class for all configuration sections with a lower case ID.
    """

    id: str = Field(description="ID (section name)", pattern=r"[a-z0-9_(),& -]+")

    @classmethod
    @override
    def generate_id(cls, name: str) -> str:
        """
        Generate an ID from a name.

        Args:
            name: Name of a section read from an INI file

        Returns:
            The ID of the section.
        """
        # Avoid circular imports

        return transform_name_to_id(name, lower=True)


# Invalid chars was taken from Antares Simulator (C++).
_sub_invalid_chars = re.compile(r"[^a-zA-Z0-9_(),& -]+").sub


def transform_name_to_id(name: str, lower: bool = True) -> str:
    """
    Transform a name into an identifier by replacing consecutive
    invalid characters by a single white space, and then whitespaces
    are striped from both ends.

    Valid characters are `[a-zA-Z0-9_(),& -]` (including space).

    Args:
        name: The name to convert.
        lower: The flag used to turn the identifier in lower case.
    """
    valid_id = _sub_invalid_chars(" ", name).strip()
    return valid_id.lower() if lower else valid_id
