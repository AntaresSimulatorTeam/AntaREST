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
import ast
import copy
from typing import Any, Optional

from antares.study.version import StudyVersion
from pydantic import ConfigDict, Field

from antarest.core.model import LowerCaseId
from antarest.core.serde import AntaresBaseModel
from antarest.study.business.model.sts_model import (
    AdditionalConstraintOperator,
    AdditionalConstraintVariable,
    Hours,
    STStorage,
    STStorageAdditionalConstraint,
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
    return storage


def serialize_st_storage(study_version: StudyVersion, storage: STStorage) -> dict[str, Any]:
    validate_st_storage_against_version(study_version, storage)
    return STStorageFileData.from_model(storage).model_dump(mode="json", by_alias=True, exclude_none=True)


##########################
# Additional constraints part
##########################


class STStorageAdditionalConstraintFileData(AntaresBaseModel):
    """
    Short-term storage additional constraint data parsed from INI file.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    cluster: LowerCaseId
    variable: AdditionalConstraintVariable
    operator: AdditionalConstraintOperator
    hours: Hours
    enabled: bool = True

    def to_ini(self) -> dict[str, Any]:
        content = self.model_dump(mode="json", exclude={"hours"})
        content["hours"] = str(self.hours)
        return content

    @staticmethod
    def from_ini(data: dict[str, Any]) -> "STStorageAdditionalConstraintFileData":
        args = copy.deepcopy(data)
        args["hours"] = list(ast.literal_eval(args["hours"]))
        return STStorageAdditionalConstraintFileData.model_validate(args)

    def to_model(self, constraint_id: str) -> STStorageAdditionalConstraint:
        return STStorageAdditionalConstraint.model_validate({"id": constraint_id, **self.model_dump(mode="json")})

    @classmethod
    def from_model(
        cls, additional_constraint: STStorageAdditionalConstraint
    ) -> "STStorageAdditionalConstraintFileData":
        return cls.model_validate(additional_constraint.model_dump(exclude={"id"}))


def parse_st_storage_additional_constraint(constraint_id: str, data: Any) -> STStorageAdditionalConstraint:
    return STStorageAdditionalConstraintFileData.from_ini(data).to_model(constraint_id)


def serialize_st_storage_additional_constraint(additional_constraint: STStorageAdditionalConstraint) -> dict[str, Any]:
    return STStorageAdditionalConstraintFileData.from_model(additional_constraint).to_ini()
