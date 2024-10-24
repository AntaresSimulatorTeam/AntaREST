# Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import typing as t

from antares.study.version import StudyVersion
from pydantic import Field

from antarest.study.business.enum_ignore_case import EnumIgnoreCase
from antarest.study.model import STUDY_VERSION_8_1
from antarest.study.storage.rawstudy.model.filesystem.config.cluster import ClusterProperties
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import IgnoreCaseIdentifier


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

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self.name}"

    @classmethod
    def _missing_(cls, value: object) -> t.Optional["RenewableClusterGroup"]:
        """
        Retrieves the default group or the matched group when an unknown value is encountered.
        """
        if isinstance(value, str):
            # Check if any group value matches the input value ignoring case sensitivity.
            # noinspection PyUnresolvedReferences
            if any(value.upper() == group.value.upper() for group in cls):
                return t.cast(RenewableClusterGroup, super()._missing_(value))
            # If a group is not found, return the default group ('OTHER1' by default).
            return cls.OTHER1
        return t.cast(t.Optional["RenewableClusterGroup"], super()._missing_(value))


class RenewableProperties(ClusterProperties):
    """
    Properties of a renewable cluster read from the configuration files.
    """

    group: RenewableClusterGroup = Field(
        title="Renewable Cluster Group",
        default=RenewableClusterGroup.OTHER1,
        description="Renewable Cluster Group",
    )

    ts_interpretation: TimeSeriesInterpretation = Field(
        title="Time Series Interpretation",
        default=TimeSeriesInterpretation.POWER_GENERATION,
        description="Time series interpretation",
        alias="ts-interpretation",
    )


class RenewableConfig(RenewableProperties, IgnoreCaseIdentifier):
    """
    Configuration of a renewable cluster.

    Usage:

    >>> from antarest.study.storage.rawstudy.model.filesystem.config.renewable import RenewableConfig

    >>> cfg = RenewableConfig(name="cluster-01")
    >>> cfg.id
    'cluster-01'
    >>> cfg.enabled
    True
    >>> cfg.ts_interpretation.value
    'power-generation'
    """


RenewableConfigType = RenewableConfig


def get_renewable_config_cls(study_version: StudyVersion) -> t.Type[RenewableConfig]:
    """
    Retrieves the renewable configuration class based on the study version.

    Args:
        study_version: The version of the study.

    Returns:
        The renewable configuration class.
    """
    if study_version >= STUDY_VERSION_8_1:
        return RenewableConfig
    raise ValueError(f"Unsupported study version {study_version}, required 810 or above.")


def create_renewable_config(study_version: StudyVersion, **kwargs: t.Any) -> RenewableConfigType:
    """
    Factory method to create a renewable configuration model.

    Args:
        study_version: The version of the study.
        **kwargs: The properties to be used to initialize the model.

    Returns:
        The renewable configuration model.

    Raises:
        ValueError: If the study version is not supported.
    """
    cls = get_renewable_config_cls(study_version)
    return cls(**kwargs)
