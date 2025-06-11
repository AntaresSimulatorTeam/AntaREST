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
from pydantic import ConfigDict, Field, model_validator

from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.string import to_kebab_case
from antarest.study.business.model.binding_constraint_model import (
    BindingConstraint,
    BindingConstraintFrequency,
    BindingConstraintOperator,
    BindingConstraintUpdate,
    ClusterTerm,
    ConstraintTerm,
    LinkTerm,
    initialize_binding_constraint,
    validate_binding_constraint_against_version,
)


class BindingConstraintFileData(AntaresBaseModel):
    """
    Binding constraint data parsed from INI file.
    """

    model_config = ConfigDict(alias_generator=to_kebab_case, extra="forbid", populate_by_name=True)

    @model_validator(mode="before")
    @classmethod
    def _validate_terms(cls, values: dict[str, Any]) -> dict[str, Any]:
        return _terms_from_ini(values)

    id: str
    name: str
    enabled: Optional[bool] = None
    time_step: Optional[BindingConstraintFrequency] = Field(None, alias="type")
    operator: Optional[BindingConstraintOperator] = None
    comments: Optional[str] = None
    terms: Optional[list[ConstraintTerm]] = None

    # Added in 8.3
    filter_year_by_year: Optional[str] = None
    filter_synthesis: Optional[str] = None

    # Added in 8.7
    group: Optional[str] = None

    def to_model(self) -> BindingConstraint:
        return BindingConstraint.model_validate(self.model_dump(exclude_none=True, exclude={"id"}))

    def to_update_model(self) -> BindingConstraintUpdate:
        return BindingConstraintUpdate.model_validate(self.model_dump(exclude_none=True, exclude={"id"}))

    @classmethod
    def from_model(cls, constraint: BindingConstraint) -> "BindingConstraintFileData":
        return cls.model_validate(constraint.model_dump())


def _terms_from_ini(data: dict[str, Any]) -> dict[str, Any]:
    """Parse terms from the INI file and remove them from the data dict."""
    terms = []
    for key in list(data.keys()):
        if "%" in key:
            area_1, area_2 = key.split("%")
            value = data.pop(key)
            weight, offset = value.split("%") if "%" in value else (value, None)
            terms.append(ConstraintTerm(weight=weight, offset=offset, data=LinkTerm(area1=area_1, area2=area_2)))
        elif "." in key:
            area, cluster = key.split(".")
            value = data.pop(key)
            weight, offset = value.split("%") if "%" in value else (value, None)
            terms.append(ConstraintTerm(weight=weight, offset=offset, data=ClusterTerm(area=area, cluster=cluster)))
    if terms:
        data["terms"] = terms
    return data


def _terms_to_ini(terms: list[ConstraintTerm]) -> dict[str, Any]:
    content = {}
    for term in terms:
        content[term.generate_id()] = term.weight if term.offset is None else f"{term.weight}%{term.offset}"
    return content


def parse_binding_constraint(study_version: StudyVersion, data: Any) -> BindingConstraint:
    bc = BindingConstraintFileData.model_validate(data).to_model()
    validate_binding_constraint_against_version(study_version, bc)
    initialize_binding_constraint(bc, study_version)
    return bc


def parse_binding_constraint_for_update(study_version: StudyVersion, data: Any) -> BindingConstraintUpdate:
    bc = BindingConstraintFileData.model_validate(data).to_update_model()
    validate_binding_constraint_against_version(study_version, bc)
    return bc


def serialize_binding_constraint(study_version: StudyVersion, constraint: BindingConstraint) -> dict[str, Any]:
    validate_binding_constraint_against_version(study_version, constraint)
    bc = BindingConstraintFileData.from_model(constraint)
    content = bc.model_dump(mode="json", by_alias=True, exclude_none=True, exclude={"terms"})
    if bc.terms:
        content.update(_terms_to_ini(bc.terms))
    return content
