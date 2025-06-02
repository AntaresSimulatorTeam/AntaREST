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
from pydantic import ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

from antarest.core.exceptions import InvalidFieldForVersionError
from antarest.core.serde import AntaresBaseModel
from antarest.study.business.enum_ignore_case import EnumIgnoreCase
from antarest.study.model import STUDY_VERSION_8_6
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.config.validation import ItemName


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
Efficiency: TypeAlias = Annotated[float, Field(ge=0, le=1)]
InitialLevel: TypeAlias = Annotated[float, Field(ge=0, le=1)]


class STStorage(AntaresBaseModel):
    """
    Short-term storage model.
    """

    model_config = ConfigDict(alias_generator=to_camel, extra="forbid", populate_by_name=True)

    name: ItemName

    @model_validator(mode="before")
    @classmethod
    def set_id(cls, data: Any) -> Any:
        if isinstance(data, dict) and "id" not in data and "name" in data:
            data["id"] = transform_name_to_id(data["name"])
        return data

    injection_nominal_capacity: Capacity = 0
    withdrawal_nominal_capacity: Capacity = 0
    reservoir_capacity: Capacity = 0
    efficiency: Efficiency = 1
    initial_level: InitialLevel = 0.5
    initial_level_optim: bool = False

    # Added in 8.8
    enabled: Optional[bool] = None

    # Added in 9.2
    group: Optional[str] = None
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
    group: Optional[str] = None
    efficiency_withdrawal: Optional[Efficiency] = None
    penalize_variation_injection: Optional[bool] = None
    penalize_variation_withdrawal: Optional[bool] = None


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
    group: Optional[str] = None
    efficiency_withdrawal: Optional[Efficiency] = None
    penalize_variation_injection: Optional[bool] = None
    penalize_variation_withdrawal: Optional[bool] = None



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
        raise InvalidFieldForVersionError(f"Short-term storages only exist since v8.8 and your study is in {version}")


        for field in ["nh3", "so2", "nox", "pm2_5", "pm5", "pm10", "nmvoc", "op1", "op2", "op3", "op4", "op5"]:
            _check_min_version(cluster_data, field, version)

    if version < STUDY_VERSION_8_7:
        for field in ["cost_generation", "efficiency", "variable_o_m_cost"]:
            _check_min_version(cluster_data, field, version)


def _initialize_field_default(cluster: ThermalCluster, field: str, default_value: Any) -> None:
    if getattr(cluster, field) is None:
        setattr(cluster, field, default_value)


def initialize_thermal_cluster(cluster: ThermalCluster, version: StudyVersion) -> None:
    """
    Set undefined version-specific fields to default values.
    """
    if version >= STUDY_VERSION_8_6:
        for field in ["nh3", "so2", "nox", "pm2_5", "pm5", "pm10", "nmvoc", "op1", "op2", "op3", "op4", "op5"]:
            _initialize_field_default(cluster, field, 0)

    if version >= STUDY_VERSION_8_7:
        _initialize_field_default(cluster, "cost_generation", ThermalCostGeneration.SET_MANUALLY)
        _initialize_field_default(cluster, "efficiency", 100.0)
        _initialize_field_default(cluster, "variable_o_m_cost", 0.0)


def create_thermal_cluster(cluster_data: ThermalClusterCreation, version: StudyVersion) -> ThermalCluster:
    """
    Creates a thermal cluster from a creation request, checking and initializing it against the specified study version.
    """
    cluster = ThermalCluster.model_validate(cluster_data.model_dump(exclude_none=True))
    validate_thermal_cluster_against_version(version, cluster_data)
    initialize_thermal_cluster(cluster, version)
    return cluster


def update_thermal_cluster(cluster: ThermalCluster, data: ThermalClusterUpdate) -> ThermalCluster:
    """
    Updates a cluster according to the provided update data.
    """
    return cluster.model_copy(update=data.model_dump(exclude_none=True))

