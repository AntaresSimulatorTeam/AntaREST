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
from typing import Annotated, Any, Optional, TypeAlias

from antares.study.version import StudyVersion
from pydantic import BeforeValidator, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

from antarest.core.exceptions import InvalidFieldForVersionError, ShortTermStorageValuesCoherenceError
from antarest.core.model import LowerCaseId, LowerCaseStr
from antarest.core.serde import AntaresBaseModel
from antarest.study.business.enum_ignore_case import EnumIgnoreCase
from antarest.study.model import STUDY_VERSION_8_6, STUDY_VERSION_8_8, STUDY_VERSION_9_2
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.config.validation import AreaId, ItemName


class STStorageGroup(EnumIgnoreCase):
    """
    This class defines the specific energy storage systems.

    Enum values:

        - PSP_OPEN: Represents an open pumped storage plant.
        - PSP_CLOSED: Represents a closed pumped storage plant.
        - PONDAGE: Represents a pondage storage system (reservoir storage system).
        - BATTERY: Represents a battery storage system.
        - OTHER1...OTHER5: Represents other energy storage systems.
    """

    PSP_OPEN = "psp_open"
    PSP_CLOSED = "psp_closed"
    PONDAGE = "pondage"
    BATTERY = "battery"
    OTHER1 = "other1"
    OTHER2 = "other2"
    OTHER3 = "other3"
    OTHER4 = "other4"
    OTHER5 = "other5"


# Validation helpers
Capacity: TypeAlias = Annotated[float, Field(ge=0)]
Efficiency: TypeAlias = Annotated[float, Field(ge=0)]
InitialLevel: TypeAlias = Annotated[float, Field(ge=0, le=1)]
Group: TypeAlias = Optional[LowerCaseStr]


class STStorage(AntaresBaseModel):
    """
    Short-term storage model.
    """

    model_config = ConfigDict(alias_generator=to_camel, extra="forbid", populate_by_name=True)

    name: ItemName
    id: str

    @model_validator(mode="before")
    @classmethod
    def set_id(cls, data: Any) -> Any:
        if isinstance(data, dict) and "id" not in data and "name" in data:
            data["id"] = transform_name_to_id(data["name"])
        return data

    group: Group = STStorageGroup.OTHER1.value
    injection_nominal_capacity: Capacity = 0
    withdrawal_nominal_capacity: Capacity = 0
    reservoir_capacity: Capacity = 0
    efficiency: Efficiency = 1
    initial_level: InitialLevel = 0.5
    initial_level_optim: bool = False

    # Added in 8.8
    enabled: Optional[bool] = None

    # Added in 9.2
    efficiency_withdrawal: Optional[Efficiency] = None
    penalize_variation_injection: Optional[bool] = None
    penalize_variation_withdrawal: Optional[bool] = None


class STStorageCreation(AntaresBaseModel):
    """
    Represents a creation request for a short-term storage.

    Most fields are optional: at creation time, default values of the short-term storage
    model will be used.
    """

    model_config = ConfigDict(alias_generator=to_camel, extra="forbid", populate_by_name=True)

    name: ItemName

    injection_nominal_capacity: Optional[Capacity] = None
    withdrawal_nominal_capacity: Optional[Capacity] = None
    reservoir_capacity: Optional[Capacity] = None
    efficiency: Optional[Efficiency] = None
    initial_level: Optional[InitialLevel] = None
    initial_level_optim: Optional[bool] = None
    enabled: Optional[bool] = None
    group: Group = None
    efficiency_withdrawal: Optional[Efficiency] = None
    penalize_variation_injection: Optional[bool] = None
    penalize_variation_withdrawal: Optional[bool] = None

    @classmethod
    def from_storage(cls, storage: STStorage) -> "STStorageCreation":
        """
        Conversion to creation request, can be useful for duplicating storages.
        """
        return STStorageCreation.model_validate(storage.model_dump(mode="json", exclude={"id"}, exclude_none=True))


class STStorageUpdate(AntaresBaseModel):
    """
    Represents an update of a short-term storage.

    Only not-None fields will be used to update the short-term storage.
    """

    model_config = ConfigDict(alias_generator=to_camel, extra="forbid", populate_by_name=True)

    @model_validator(mode="before")
    @classmethod
    def _ignore_name(cls, data: Any) -> Any:
        """
        Renaming is not currently supported, but name needs to be accepted
        for backwards compatibility. We can restore that property when
        proper renaming is implemented.
        """
        if isinstance(data, dict) and "name" in data:
            del data["name"]
        return data

    injection_nominal_capacity: Optional[Capacity] = None
    withdrawal_nominal_capacity: Optional[Capacity] = None
    reservoir_capacity: Optional[Capacity] = None
    efficiency: Optional[Efficiency] = None
    initial_level: Optional[InitialLevel] = None
    initial_level_optim: Optional[bool] = None
    enabled: Optional[bool] = None
    group: Group = None
    efficiency_withdrawal: Optional[Efficiency] = None
    penalize_variation_injection: Optional[bool] = None
    penalize_variation_withdrawal: Optional[bool] = None


STStorageUpdates = dict[LowerCaseId, dict[LowerCaseId, STStorageUpdate]]


def _check_min_version(data: Any, field: str, version: StudyVersion) -> None:
    if getattr(data, field) is not None:
        raise InvalidFieldForVersionError(f"Field {field} is not a valid field for study version {version}")


def validate_st_storage_against_version(
    version: StudyVersion,
    storage_data: STStorage | STStorageCreation | STStorageUpdate,
) -> None:
    """
    Validates input short-term storage data against the provided study versions

    Will raise an InvalidFieldForVersionError if a field is not valid for the given study version.
    """
    if version < STUDY_VERSION_8_6:
        raise InvalidFieldForVersionError(f"Short-term storages only exist since v8.6 and your study is in {version}")

    if storage_data.group is not None and version < STUDY_VERSION_9_2:
        # We need to be sure we're able to cast the group to a STStorageGroup enum value
        if storage_data.group not in [e.value for e in STStorageGroup]:
            raise InvalidFieldForVersionError(f"Free groups are available since v9.2 and your study is in {version}")

    if version < STUDY_VERSION_8_8:
        _check_min_version(storage_data, "enabled", version)

    if version < STUDY_VERSION_9_2:
        for field in ["efficiency_withdrawal", "penalize_variation_injection", "penalize_variation_withdrawal"]:
            _check_min_version(storage_data, field, version)


def _initialize_field_default(storage: STStorage, field: str, default_value: Any) -> None:
    if getattr(storage, field) is None:
        setattr(storage, field, default_value)


def initialize_st_storage(storage: STStorage, version: StudyVersion) -> None:
    """
    Set undefined version-specific fields to default values.
    """
    if version >= STUDY_VERSION_8_6:
        for field in ["injection_nominal_capacity", "withdrawal_nominal_capacity", "reservoir_capacity"]:
            _initialize_field_default(storage, field, 0)
        _initialize_field_default(storage, "efficiency", 1)
        _initialize_field_default(storage, "initial_level", 0.5)
        _initialize_field_default(storage, "initial_level_optim", False)

    if version >= STUDY_VERSION_8_8:
        _initialize_field_default(storage, "enabled", True)

    if version >= STUDY_VERSION_9_2:
        _initialize_field_default(storage, "efficiency_withdrawal", 1)
        _initialize_field_default(storage, "penalize_variation_injection", False)
        _initialize_field_default(storage, "penalize_variation_withdrawal", False)


def check_attributes_coherence(storage: STStorage, version: StudyVersion) -> None:
    """
    The Simulator performs this business logic before running the simulation.
    It prevents the user from creating a storage that creates energy out of thin air.
    """
    if version < STUDY_VERSION_9_2:
        if storage.efficiency > 1:
            raise ShortTermStorageValuesCoherenceError(
                storage.id, f"Prior to v9.2, efficiency must be lower than 1 and was {storage.efficiency}"
            )
    else:
        efficiency_withdrawal = 1 if storage.efficiency_withdrawal is None else storage.efficiency_withdrawal
        if storage.efficiency > efficiency_withdrawal:
            raise ShortTermStorageValuesCoherenceError(
                storage.id,
                f"efficiency must be lower than efficiency_withdrawal. Currently: {storage.efficiency} > {efficiency_withdrawal}",
            )


def create_st_storage(cluster_data: STStorageCreation, version: StudyVersion) -> STStorage:
    """
    Creates a short-term storage from a creation request, checking and initializing it against the specified study version.
    """
    storage = STStorage.model_validate(cluster_data.model_dump(exclude_none=True))
    validate_st_storage_against_version(version, cluster_data)
    initialize_st_storage(storage, version)
    check_attributes_coherence(storage, version)
    return storage


def update_st_storage(storage: STStorage, data: STStorageUpdate, version: StudyVersion) -> STStorage:
    """
    Updates a short-term storage according to the provided update data.
    """
    storage = storage.model_copy(update=data.model_dump(exclude_none=True))
    check_attributes_coherence(storage, version)
    return storage


##########################
# Additional constraints part
##########################


class AdditionalConstraintVariable(EnumIgnoreCase):
    WITHDRAWAL = "withdrawal"
    INJECTION = "injection"
    NETTING = "netting"


class AdditionalConstraintOperator(EnumIgnoreCase):
    LESS = "less"
    GREATER = "greater"
    EQUAL = "equal"


def check_hours_compliance(value: int) -> int:
    if not isinstance(value, int) or not (0 <= value <= 168):
        raise ValueError(f"Hours must be integers between 0 and 168, got {value}")
    return value


WeekHour: TypeAlias = Annotated[int, BeforeValidator(check_hours_compliance)]


class Occurence(AntaresBaseModel):
    hours: list[WeekHour]


class STStorageAdditionalConstraint(AntaresBaseModel):
    """
    Short-term storage additional constraints model.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    @model_validator(mode="before")
    @classmethod
    def set_id(cls, data: dict[str, Any]) -> dict[str, Any]:
        data["id"] = transform_name_to_id(data["name"])
        return data

    id: str
    name: ItemName
    variable: AdditionalConstraintVariable = AdditionalConstraintVariable.NETTING
    operator: AdditionalConstraintOperator = AdditionalConstraintOperator.LESS
    occurences: list[Occurence] = []
    enabled: bool = True


class STStorageAdditionalConstraintCreation(AntaresBaseModel):
    """
    Represents a creation request for a short-term storage additional constraint.

    Most fields are optional: at creation time, default values of the constraint will be used.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: ItemName
    variable: Optional[AdditionalConstraintVariable] = None
    operator: Optional[AdditionalConstraintOperator] = None
    occurences: Optional[list[Occurence]] = None
    enabled: Optional[bool] = None


class STStorageAdditionalConstraintUpdate(AntaresBaseModel):
    """
    Represents an update of a short-term storage additional constraint.

    Only not-None fields will be used to update the constraint.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    variable: Optional[AdditionalConstraintVariable] = None
    operator: Optional[AdditionalConstraintOperator] = None
    occurences: Optional[list[Occurence]] = None
    enabled: Optional[bool] = None


STStorageAdditionalConstraintsMap = dict[AreaId, dict[LowerCaseId, list[STStorageAdditionalConstraint]]]

# 2nd key corresponds to a short-term storage id and 3rd to the constraint id.
STStorageAdditionalConstraintUpdates = dict[
    AreaId, dict[LowerCaseId, dict[LowerCaseId, STStorageAdditionalConstraintUpdate]]
]


def create_st_storage_constraint(cluster_data: STStorageAdditionalConstraintCreation) -> STStorageAdditionalConstraint:
    """
    Creates a short-term storage constraint from a creation request
    """
    args = cluster_data.model_dump(exclude_none=True)
    return STStorageAdditionalConstraint.model_validate(args)


def update_st_storage_constraint(
    constraint: STStorageAdditionalConstraint, data: STStorageAdditionalConstraintUpdate
) -> STStorageAdditionalConstraint:
    """
    Updates a short-term storage constraint according to the provided update data.
    """
    current_constraint = constraint.model_dump(mode="json")
    update_constraint = data.model_dump(mode="json", exclude_none=True)
    current_constraint.update(update_constraint)
    return STStorageAdditionalConstraint.model_validate(current_constraint)
