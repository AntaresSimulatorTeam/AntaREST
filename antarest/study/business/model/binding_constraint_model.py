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

from typing import Any, Dict, List, Optional, TypeAlias

from antares.study.version import StudyVersion
from pydantic import ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

from antarest.core.exceptions import InvalidConstraintTerm, InvalidFieldForVersionError
from antarest.core.model import LowerCaseId, LowerCaseStr
from antarest.core.serde import AntaresBaseModel
from antarest.study.business.enum_ignore_case import EnumIgnoreCase
from antarest.study.business.model.common import FILTER_VALUES, CommaSeparatedFilterOptions
from antarest.study.model import STUDY_VERSION_8_3, STUDY_VERSION_8_7
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.config.validation import ItemName


class BindingConstraintFrequency(EnumIgnoreCase):
    """
    Frequency of a binding constraint.

    Attributes:
        HOURLY: hourly time series with 8784 lines
        DAILY: daily time series with 366 lines
        WEEKLY: weekly time series with 366 lines (same as daily)
    """

    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"


class BindingConstraintOperator(EnumIgnoreCase):
    """
    Operator of a binding constraint.

    Attributes:
        LESS: less than or equal to
        GREATER: greater than or equal to
        BOTH: both LESS and GREATER
        EQUAL: equal to
    """

    LESS = "less"
    GREATER = "greater"
    BOTH = "both"
    EQUAL = "equal"


OPERATOR_MATRICES_MAP: Dict[BindingConstraintOperator, List[str]] = {
    BindingConstraintOperator.EQUAL: ["eq"],
    BindingConstraintOperator.GREATER: ["gt"],
    BindingConstraintOperator.LESS: ["lt"],
    BindingConstraintOperator.BOTH: ["lt", "gt"],
}

OPERATOR_MATRIX_FILE_MAP = {
    BindingConstraintOperator.EQUAL: ["{bc_id}_eq"],
    BindingConstraintOperator.GREATER: ["{bc_id}_gt"],
    BindingConstraintOperator.LESS: ["{bc_id}_lt"],
    BindingConstraintOperator.BOTH: ["{bc_id}_lt", "{bc_id}_gt"],
}

DEFAULT_GROUP = "default"
"""Default group for binding constraints (since v8.7)."""
DEFAULT_OPERATOR = BindingConstraintOperator.EQUAL
DEFAULT_TIMESTEP = BindingConstraintFrequency.HOURLY

# ==================================================
# Binding constraint matrices
# ==================================================

MatrixType: TypeAlias = List[List[float]]


class BindingConstraintMatrices(AntaresBaseModel):
    """
    Class used to store the matrices of a binding constraint.
    """

    model_config = ConfigDict(alias_generator=to_camel, extra="forbid", populate_by_name=True)

    values: Optional[MatrixType | str] = Field(
        default=None,
        description="2nd member matrix for studies before v8.7",
    )
    less_term_matrix: Optional[MatrixType | str] = Field(
        default=None,
        description="less term matrix for v8.7+ studies",
    )
    greater_term_matrix: Optional[MatrixType | str] = Field(
        default=None,
        description="greater term matrix for v8.7+ studies",
    )
    equal_term_matrix: Optional[MatrixType | str] = Field(
        default=None,
        description="equal term matrix for v8.7+ studies",
    )

    @model_validator(mode="before")
    def check_matrices(cls, values: Dict[str, Optional[MatrixType | str]]) -> Dict[str, Optional[MatrixType | str]]:
        values_matrix = values.get("values") or None
        less_term_matrix = values.get("less_term_matrix") or None
        greater_term_matrix = values.get("greater_term_matrix") or None
        equal_term_matrix = values.get("equal_term_matrix") or None
        if values_matrix and (less_term_matrix or greater_term_matrix or equal_term_matrix):
            raise ValueError(
                "You cannot fill 'values' (matrix before v8.7) and a matrix term:"
                " 'less_term_matrix', 'greater_term_matrix' or 'equal_term_matrix' (matrices since v8.7)"
            )

        return values


# ==================================================
# Binding constraint terms
# ==================================================


def validate_and_transform_term_id(term_id: str) -> str:
    """
    Used to validate the term id given by the user when updating an existing one
    """
    try:
        if "%" in term_id:
            area_1, area_2 = sorted(term_id.split("%"))
            return f"{transform_name_to_id(area_1)}%{transform_name_to_id(area_2)}"
        elif "." in term_id:
            area, cluster = term_id.split(".")
            return f"{transform_name_to_id(area)}.{transform_name_to_id(cluster)}"
        raise InvalidConstraintTerm(term_id, "Your term id is not well-formatted")
    except Exception:
        raise InvalidConstraintTerm(term_id, "Your term id is not well-formatted")


class LinkTerm(AntaresBaseModel):
    """
    DTO for a constraint term on a link between two areas.

    Attributes:
        area1: the first area ID
        area2: the second area ID
    """

    area1: LowerCaseId
    area2: LowerCaseId

    def generate_id(self) -> str:
        """Return the constraint term ID for this link, of the form "area1%area2"."""
        # Ensure IDs are in alphabetical order and lower case
        ids = sorted((self.area1, self.area2))
        return "%".join(ids)


class ClusterTerm(AntaresBaseModel):
    """
    DTO for a constraint term on a cluster in an area.

    Attributes:
        area: the area ID
        cluster: the cluster ID
    """

    area: LowerCaseId
    cluster: LowerCaseId

    def generate_id(self) -> str:
        """Return the constraint term ID for this Area/cluster constraint, of the form "area.cluster"."""
        # Ensure IDs are in lower case
        return ".".join([self.area, self.cluster])


class ConstraintTermUpdate(AntaresBaseModel):
    """
    DTO used to update an existing constraint term.

    Attributes:
        id: the constraint term ID, of the form "area1%area2" or "area.cluster".
        weight: the constraint term weight, if any.
        offset: the constraint term offset, if any.
        data: the constraint term data (link or cluster), if any.
    """

    id: str
    weight: Optional[float] = None
    offset: Optional[int] = None
    data: Optional[LinkTerm | ClusterTerm] = None

    @model_validator(mode="before")
    def validate_term_id(cls, values: dict[str, Any]) -> dict[str, Any]:
        if "id" not in values:
            if "data" not in values:
                raise InvalidConstraintTerm("", "You should provide an id or data when updating an existing term")

            data = values["data"]
            if "area1" in data:
                values["id"] = "%".join((data["area1"], data["area2"]))
            elif "cluster" in data:
                values["id"] = ".".join([data["area"], data["cluster"]])
            else:
                raise InvalidConstraintTerm(str(data), "Your term data is not well-formatted")

        values["id"] = validate_and_transform_term_id(values["id"])
        return values


class ConstraintTerm(AntaresBaseModel):
    weight: float
    offset: Optional[int] = None
    data: LinkTerm | ClusterTerm

    def generate_id(self) -> str:
        return self.data.generate_id()

    def update_from(self, updated_term: ConstraintTermUpdate) -> "ConstraintTerm":
        if updated_term.weight:
            self.weight = updated_term.weight

        if updated_term.data:
            self.data = updated_term.data

        # IMPORTANT: If the user didn't give an offset it means he wants to remove it.
        self.offset = updated_term.offset

        return self


# ==================================================
# Binding constraint objects
# ==================================================


class BindingConstraint(AntaresBaseModel):
    """
    Binding constraint model.
    """

    model_config = ConfigDict(alias_generator=to_camel, extra="forbid", populate_by_name=True)

    @model_validator(mode="before")
    @classmethod
    def set_id(cls, data: Any) -> Any:
        if isinstance(data, dict) and "id" not in data and "name" in data:
            data["id"] = transform_name_to_id(data["name"])
        return data

    id: str
    name: str
    enabled: bool = True
    time_step: BindingConstraintFrequency = Field(DEFAULT_TIMESTEP, alias="type")
    operator: BindingConstraintOperator = DEFAULT_OPERATOR
    comments: str = ""
    terms: list[ConstraintTerm] = []

    # Added in 8.3
    filter_year_by_year: Optional[CommaSeparatedFilterOptions] = None
    filter_synthesis: Optional[CommaSeparatedFilterOptions] = None

    # Added in 8.7
    group: Optional[LowerCaseStr] = None


class BindingConstraintCreation(BindingConstraintMatrices):
    """
    Represents a creation request for a binding constraint.

    Most fields are optional: at creation time, default values of the constraint model will be used.
    """

    name: ItemName
    enabled: Optional[bool] = None
    time_step: BindingConstraintFrequency = Field(DEFAULT_TIMESTEP, alias="type")
    operator: Optional[BindingConstraintOperator] = None
    comments: Optional[str] = None
    terms: Optional[list[ConstraintTerm]] = None

    # Added in 8.3
    filter_year_by_year: Optional[CommaSeparatedFilterOptions] = None
    filter_synthesis: Optional[CommaSeparatedFilterOptions] = None

    # Added in 8.7
    group: Optional[LowerCaseStr] = None

    @classmethod
    def from_constraint(cls, constraint: BindingConstraint) -> "BindingConstraintCreation":
        """
        Conversion to creation request, can be useful for duplicating constraints.
        """
        return BindingConstraintCreation.model_validate(
            constraint.model_dump(mode="json", exclude={"id"}, exclude_none=True)
        )


class BindingConstraintUpdate(AntaresBaseModel):
    """
    Represents an update of a binding constraint.

    Only not-None fields will be used to update the constraint.
    """

    enabled: Optional[bool] = None
    time_step: Optional[BindingConstraintFrequency] = Field(None, alias="type")
    operator: Optional[BindingConstraintOperator] = None
    comments: Optional[str] = None
    terms: Optional[list[ConstraintTerm]] = None

    # Added in 8.3
    filter_year_by_year: Optional[CommaSeparatedFilterOptions] = None
    filter_synthesis: Optional[CommaSeparatedFilterOptions] = None

    # Added in 8.7
    group: Optional[LowerCaseStr] = None

class BindingConstraintUpdateWithMatrices(BindingConstraintUpdate, BindingConstraintMatrices):
    """
    Used inside the update endpoint and there only
    """

    def matrices(self) -> BindingConstraintMatrices:
        return BindingConstraintMatrices.model_validate(self.model_dump(mode="json", include=set(BindingConstraintMatrices.model_fields)))

    def update_model(self) -> BindingConstraintUpdate:
        return BindingConstraintUpdate.model_validate(self.model_dump(mode="json", include=set(BindingConstraintUpdate.model_fields)))


BindingConstraintUpdates = dict[LowerCaseId, BindingConstraintUpdate]


def _check_min_version(data: Any, field: str, version: StudyVersion) -> None:
    if getattr(data, field) is not None:
        raise InvalidFieldForVersionError(f"Field {field} is not a valid field for study version {version}")


def validate_binding_constraint_against_version(
    version: StudyVersion,
    constraint_data: BindingConstraint | BindingConstraintCreation | BindingConstraintUpdate,
) -> None:
    """
    Validates input binding constraint data against the provided study versions

    Will raise an InvalidFieldForVersionError if a field is not valid for the given study version.
    """

    if version < STUDY_VERSION_8_3:
        for field in ["filter_year_by_year", "filter_synthesis"]:
            _check_min_version(constraint_data, field, version)

    if version < STUDY_VERSION_8_7:
        _check_min_version(constraint_data, "group", version)


def _initialize_field_default(constraint: BindingConstraint, field: str, default_value: Any) -> None:
    if getattr(constraint, field) is None:
        setattr(constraint, field, default_value)


def initialize_binding_constraint(constraint: BindingConstraint, version: StudyVersion) -> None:
    """
    Set undefined version-specific fields to default values.
    """
    if version >= STUDY_VERSION_8_3:
        for field in ["filter_year_by_year", "filter_synthesis"]:
            _initialize_field_default(constraint, field, FILTER_VALUES)

    if version >= STUDY_VERSION_8_7:
        _initialize_field_default(constraint, "group", DEFAULT_GROUP)


def create_binding_constraint(constraint_data: BindingConstraintCreation, version: StudyVersion) -> BindingConstraint:
    """
    Creates a binding constraint from a creation request, checking and initializing it against the specified study version.
    """
    constraint = BindingConstraint.model_validate(constraint_data.model_dump(exclude_none=True))
    validate_binding_constraint_against_version(version, constraint_data)
    initialize_binding_constraint(constraint, version)
    return constraint


def update_binding_constraint(constraint: BindingConstraint, data: BindingConstraintUpdate) -> BindingConstraint:
    """
    Updates a binding constraint according to the provided update data.
    """
    return constraint.model_copy(update=data.model_dump(exclude_none=True))
