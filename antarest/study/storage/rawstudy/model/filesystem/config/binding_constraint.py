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
Object model used to read and update binding constraint configuration.
"""

from typing import Any, Optional

from antares.study.version import StudyVersion
from pydantic import ConfigDict, Field

from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.string import to_kebab_case
from antarest.study.business.model.binding_constraint_model import (
    BindingConstraint,
    BindingConstraintFrequency,
    BindingConstraintOperator,
    initialize_binding_constraint,
    validate_binding_constraint_against_version,
)


class BindingConstraintFileData(AntaresBaseModel):
    """
    Binding constraint data parsed from INI file.
    """

    model_config = ConfigDict(alias_generator=to_kebab_case, extra="forbid", populate_by_name=True)

    enabled: Optional[bool] = None
    time_step: Optional[BindingConstraintFrequency] = Field(None, alias="type")
    operator: Optional[BindingConstraintOperator] = None
    comments: Optional[str] = None

    # Added in 8.3
    filter_year_by_year: Optional[str] = None
    filter_synthesis: Optional[str] = None

    # Added in 8.7
    group: Optional[str] = None

    def to_model(self) -> BindingConstraint:
        return BindingConstraint.model_validate(self.model_dump(exclude_none=True))

    @classmethod
    def from_model(cls, constraint: BindingConstraint) -> "BindingConstraintFileData":
        return cls.model_validate(constraint.model_dump(exclude={"id"}))


def parse_binding_constraint(study_version: StudyVersion, data: Any) -> BindingConstraint:
    bc = BindingConstraintFileData.model_validate(data).to_model()
    validate_binding_constraint_against_version(study_version, bc)
    initialize_binding_constraint(bc, study_version)
    return bc


def serialize_binding_constraint(study_version: StudyVersion, constraint: BindingConstraint) -> dict[str, Any]:
    validate_binding_constraint_against_version(study_version, constraint)
    return BindingConstraintFileData.from_model(constraint).model_dump(mode="json", by_alias=True, exclude_none=True)
