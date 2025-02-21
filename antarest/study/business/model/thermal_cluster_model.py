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
from antarest.study.storage.rawstudy.model.filesystem.config.thermal import (
    Thermal870Config,
    Thermal870Properties,
    ThermalPropertiesType,
    create_thermal_properties,
)


@all_optional_model
@camel_case_model
class ThermalClusterUpdate(Thermal870Properties):
    """
    Model representing the data structure required to edit an existing thermal cluster within a study.
    """


@camel_case_model
class ThermalClusterCreation(ThermalClusterUpdate):
    """
    Model representing the data structure required to create a new thermal cluster within a study.
    """

    # noinspection Pydantic
    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, name: Optional[str]) -> str:
        """
        Validator to check if the name is not empty.
        """
        if not name:
            raise ValueError("name must not be empty")
        return name

    def to_properties(self, study_version: StudyVersion) -> ThermalPropertiesType:
        values = self.model_dump(mode="json", by_alias=False, exclude_none=True)
        return create_thermal_properties(study_version=study_version, data=values)


@all_optional_model
@camel_case_model
class ThermalClusterOutput(Thermal870Config):
    """
    Model representing the output data structure to display the details of a thermal cluster within a study.
    """
