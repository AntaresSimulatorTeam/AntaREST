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
from pydantic import BeforeValidator, ConfigDict, Field, PlainSerializer

from antarest.core.model import LowerCaseId
from antarest.core.serde import AntaresBaseModel
from antarest.study.business.model.sts_model import (
    HOURS_TYPE,
    AdditionalConstraintOperator,
    AdditionalConstraintVariable,
    STStorage,
    STStorageAdditionalConstraint,
    check_attributes_coherence,
    hours_parser,
    initialize_st_storage,
    validate_st_storage_against_version,
)


class STStorageFileData(AntaresBaseModel):
    """
    Short-term storage data parsed from INI file.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: str
    group: Optional[str] = None
    injection_nominal_capacity: Optional[float] = Field(default=None, alias="injectionnominalcapacity")
    withdrawal_nominal_capacity: Optional[float] = Field(default=None, alias="withdrawalnominalcapacity")
    reservoir_capacity: Optional[float] = Field(default=None, alias="reservoircapacity")
    efficiency: Optional[float] = None
    initial_level: Optional[float] = Field(default=None, alias="initiallevel")
    initial_level_optim: Optional[bool] = Field(default=None, alias="initialleveloptim")

    # Added in 8.8
    enabled: Optional[bool] = None

    # Added in 9.2
    efficiency_withdrawal: Optional[float] = Field(default=None, alias="efficiencywithdrawal")
    penalize_variation_injection: Optional[bool] = Field(default=None, alias="penalize-variation-injection")
    penalize_variation_withdrawal: Optional[bool] = Field(default=None, alias="penalize-variation-withdrawal")

    def to_model(self) -> STStorage:
        return STStorage.model_validate(self.model_dump(exclude_none=True))

    @classmethod
    def from_model(cls, storage: STStorage) -> "STStorageFileData":
        return cls.model_validate(storage.model_dump(exclude={"id"}))


def parse_st_storage(study_version: StudyVersion, data: Any) -> STStorage:
    storage = STStorageFileData.model_validate(data).to_model()
    validate_st_storage_against_version(study_version, storage)
    initialize_st_storage(storage, study_version)
    check_attributes_coherence(storage, study_version)
    return storage


def serialize_st_storage(study_version: StudyVersion, storage: STStorage) -> dict[str, Any]:
    validate_st_storage_against_version(study_version, storage)
    check_attributes_coherence(storage, study_version)
    return STStorageFileData.from_model(storage).model_dump(mode="json", by_alias=True, exclude_none=True)


##########################
# Additional constraints part
##########################


def _hours_serializer(value: HOURS_TYPE) -> str:
    return ", ".join(str(v) for v in value)


HoursIni: TypeAlias = Annotated[HOURS_TYPE, BeforeValidator(hours_parser), PlainSerializer(_hours_serializer)]


class STStorageAdditionalConstraintFileData(AntaresBaseModel):
    """
    Short-term storage additional constraint data parsed from INI file.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    cluster: LowerCaseId
    variable: AdditionalConstraintVariable
    operator: AdditionalConstraintOperator
    hours: HoursIni
    enabled: bool = True

    def to_model(self, constraint_id: str) -> tuple[str, STStorageAdditionalConstraint]:
        args = {"id": constraint_id, **self.model_dump(mode="json", exclude={"cluster"})}
        return self.cluster, STStorageAdditionalConstraint.model_validate(args)

    @classmethod
    def from_model(
        cls, storage_id: str, additional_constraint: STStorageAdditionalConstraint
    ) -> "STStorageAdditionalConstraintFileData":
        return cls.model_validate({"cluster": storage_id, **additional_constraint.model_dump(exclude={"id"})})


def parse_st_storage_additional_constraint(constraint_id: str, data: Any) -> tuple[str, STStorageAdditionalConstraint]:
    return STStorageAdditionalConstraintFileData.model_validate(data).to_model(constraint_id)


def serialize_st_storage_additional_constraint(
    storage_id: str, additional_constraint: STStorageAdditionalConstraint
) -> dict[str, Any]:
    return STStorageAdditionalConstraintFileData.from_model(storage_id, additional_constraint).model_dump(mode="json")
