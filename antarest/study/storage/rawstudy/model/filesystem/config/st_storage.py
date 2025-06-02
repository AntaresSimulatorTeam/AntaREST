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
from typing import Any, Optional

from antares.study.version import StudyVersion
from pydantic import ConfigDict, Field

from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.string import to_kebab_case
from antarest.study.business.model.sts_model import STStorage
from antarest.study.business.model.thermal_cluster_model import (
    initialize_thermal_cluster,
    validate_thermal_cluster_against_version,
)


class STStorageFileData(AntaresBaseModel):
    """
    Short-term storage data parsed from INI file.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: str
    injection_nominal_capacity: Optional[float] = Field(default=None, alias="injectionnominalcapacity")
    withdrawal_nominal_capacity: Optional[float] = Field(default=None, alias="withdrawalnominalcapacity")
    reservoir_capacity: Optional[float] = Field(default=None, alias="reservoircapacity")
    efficiency: Optional[float] = None
    initial_level: Optional[float] = Field(default=None, alias="initiallevel")
    initial_level_optim: Optional[float] = Field(default=None, alias="initialleveloptim")

    # Added in 8.8
    enabled: Optional[bool] = None

    # Added in 9.2
    group: Optional[str] = None

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
    validate_thermal_cluster_against_version(study_version, storage)
    initialize_thermal_cluster(storage, study_version)
    return storage


def serialize_st_storage(study_version: StudyVersion, storage: STStorage) -> dict[str, Any]:
    validate_thermal_cluster_against_version(study_version, storage)
    return STStorageFileData.from_model(storage).model_dump(mode="json", by_alias=True, exclude_none=True)
