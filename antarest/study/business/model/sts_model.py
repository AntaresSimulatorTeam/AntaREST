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
from typing import Optional

from antares.study.version import StudyVersion
from pydantic import field_validator

from antarest.study.business.all_optional_meta import all_optional_model, camel_case_model
from antarest.study.storage.rawstudy.model.filesystem.config.st_storage import (
    STStorage880Config,
    STStorage880Properties,
    STStoragePropertiesType,
    create_st_storage_properties,
)


@all_optional_model
@camel_case_model
class STStorageUpdate(STStorage880Properties):
    """
    Model representing the form used to EDIT an existing short-term storage.
    """

    class Config:
        populate_by_name = True


class STStorageCreation(STStorageUpdate):
    """
    Model representing the form used to CREATE a new short-term storage.
    """

    # noinspection Pydantic
    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, name: Optional[str]) -> str:
        """
        Validator to check if the name is not empty.
        """
        if not name:
            raise ValueError("'name' must not be empty")
        return name

    def to_properties(self, version: StudyVersion) -> STStoragePropertiesType:
        return create_st_storage_properties(study_version=version, data=self.model_dump(mode="json", exclude_none=True))


@camel_case_model
class STStorageOutput(STStorage880Config):
    """
    Model representing the form used to display the details of a short-term storage entry.
    """
