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

import typing as t

from pydantic import Field, model_validator

__all__ = "LowerCaseIdentifier"

from antarest.core.serialization import AntaresBaseModel
from antarest.study.storage.rawstudy.model.filesystem.config.field_validators import transform_name_to_id


class LowerCaseIdentifier(
    AntaresBaseModel,
    extra="forbid",
    validate_assignment=True,
    populate_by_name=True,
):
    """
    Base class for all configuration sections with an ID.
    """

    id: str = Field(description="ID (section name)", pattern=r"[a-zA-Z0-9_(),& -]+")

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
                values["id"] = transform_name_to_id(storage_id)
                return values
            if not values.get("name"):
                return values
            name = values["name"]
            if storage_id := transform_name_to_id(name):
                values["id"] = storage_id
            else:
                raise ValueError(f"Invalid name '{name}'.")
        return values
