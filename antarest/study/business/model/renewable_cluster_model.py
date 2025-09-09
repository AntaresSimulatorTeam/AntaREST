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
from typing import Any, Optional, TypeAlias, cast

from antares.study.version import StudyVersion
from pydantic import ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel
from typing_extensions import override

from antarest.core.model import LowerCaseId, LowerCaseStr
from antarest.core.serde import AntaresBaseModel
from antarest.study.business.enum_ignore_case import EnumIgnoreCase
from antarest.study.model import STUDY_VERSION_9_3
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.config.validation import ItemName


class TimeSeriesInterpretation(EnumIgnoreCase):
    """
    Timeseries mode:

    - Power generation means that the unit of the timeseries is in MW,
    - Production factor means that the unit of the timeseries is in p.u.
      (between 0 and 1, 1 meaning the full installed capacity)
    """

    POWER_GENERATION = "power-generation"
    PRODUCTION_FACTOR = "production-factor"


class RenewableClusterGroup(EnumIgnoreCase):
    """
    Renewable cluster groups.

    The group can be any one of the following:
    "Wind Onshore", "Wind Offshore", "Solar Thermal", "Solar PV", "Solar Rooftop",
    "Other RES 1", "Other RES 2", "Other RES 3", or "Other RES 4".
    If not specified, the renewable cluster will be part of the group "Other RES 1".
    """

    THERMAL_SOLAR = "solar thermal"
    PV_SOLAR = "solar pv"
    ROOFTOP_SOLAR = "solar rooftop"
    WIND_ON_SHORE = "wind onshore"
    WIND_OFF_SHORE = "wind offshore"
    OTHER1 = "other res 1"
    OTHER2 = "other res 2"
    OTHER3 = "other res 3"
    OTHER4 = "other res 4"

    @override
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self.name}"

    @classmethod
    @override
    def _missing_(cls, value: object) -> Optional["RenewableClusterGroup"]:
        """
        Retrieves the default group or the matched group when an unknown value is encountered.
        """
        if isinstance(value, str):
            # Check if any group value matches the input value ignoring case sensitivity.
            # noinspection PyUnresolvedReferences
            if any(value.lower() == group.value for group in cls):
                return cast(RenewableClusterGroup, super()._missing_(value))
            # If a group is not found, return the default group ('OTHER1' by default).
            return cls.OTHER1
        return cast(Optional["RenewableClusterGroup"], super()._missing_(value))


Group: TypeAlias = Optional[LowerCaseStr]


class RenewableCluster(AntaresBaseModel):
    """
    Renewable cluster model.
    """

    model_config = ConfigDict(alias_generator=to_camel, extra="forbid", populate_by_name=True)

    # TODO: for backwards compat, we do not set ID in lower case, but we should change this
    @model_validator(mode="before")
    @classmethod
    def set_id(cls, data: Any) -> Any:
        if isinstance(data, dict) and "id" not in data and "name" in data:
            data["id"] = transform_name_to_id(data["name"], lower=False)
        return data

    id: str
    name: ItemName
    enabled: bool = True
    unit_count: int = Field(default=1, ge=1)
    nominal_capacity: float = Field(default=0.0, ge=0)
    group: Group = RenewableClusterGroup.OTHER1.value
    ts_interpretation: TimeSeriesInterpretation = TimeSeriesInterpretation.POWER_GENERATION


class RenewableClusterCreation(AntaresBaseModel):
    """
    Represents a creation request for a renewable cluster.

    Most fields are optional: at creation time, default values of the renewable cluster model will be used.
    """

    model_config = ConfigDict(alias_generator=to_camel, extra="forbid", populate_by_name=True)

    name: ItemName
    enabled: Optional[bool] = None
    unit_count: Optional[int] = Field(default=None, ge=1)
    nominal_capacity: Optional[float] = Field(default=None, ge=0)
    group: Group = None
    ts_interpretation: Optional[TimeSeriesInterpretation] = None

    @classmethod
    def from_cluster(cls, cluster: RenewableCluster) -> "RenewableClusterCreation":
        """
        Conversion to creation request
        """
        return RenewableClusterCreation.model_validate(
            cluster.model_dump(mode="json", exclude={"id"}, exclude_none=True)
        )


class RenewableClusterUpdate(AntaresBaseModel):
    """
    Represents an update of a thermal cluster.

    Only not-None fields will be used to update the thermal cluster.
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

    enabled: Optional[bool] = None
    unit_count: Optional[int] = Field(default=None, ge=1)
    nominal_capacity: Optional[float] = Field(default=None, ge=0)
    group: Group = None
    ts_interpretation: Optional[TimeSeriesInterpretation] = None


RenewableClusterUpdates = dict[LowerCaseId, dict[LowerCaseId, RenewableClusterUpdate]]


def validate_renewable_cluster_against_version(
    version: StudyVersion,
    cluster_data: RenewableCluster | RenewableClusterCreation | RenewableClusterUpdate,
) -> None:
    """
    Validates input renewable cluster data against the provided study versions

    Will raise an InvalidFieldForVersionError if a field is not valid for the given study version.
    """
    if cluster_data.group is not None and version < STUDY_VERSION_9_3:
        # Performs this transformation to fit with old behavior
        # Before, when giving a fake group, we used to write `other res 1` instead and not crash.
        cluster_data.group = RenewableClusterGroup(cluster_data.group)


def create_renewable_cluster(cluster_data: RenewableClusterCreation, version: StudyVersion) -> RenewableCluster:
    """
    Creates a renewable cluster from a creation request
    """
    validate_renewable_cluster_against_version(version, cluster_data)
    return RenewableCluster.model_validate(cluster_data.model_dump(exclude_none=True))


def update_renewable_cluster(cluster: RenewableCluster, data: RenewableClusterUpdate) -> RenewableCluster:
    """
    Updates a renewable cluster according to the provided update data.
    """
    return cluster.model_copy(update=data.model_dump(exclude_none=True))
