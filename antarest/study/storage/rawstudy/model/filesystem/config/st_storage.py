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

import typing as t
from typing import Any, Dict

from antares.study.version import StudyVersion
from pydantic import Field

from antarest.study.business.enum_ignore_case import EnumIgnoreCase
from antarest.study.model import STUDY_VERSION_8_6, STUDY_VERSION_8_8
from antarest.study.storage.rawstudy.model.filesystem.config.cluster import ItemProperties
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import LowerCaseIdentifier, transform_name_to_id


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


# noinspection SpellCheckingInspection
class STStorageProperties(ItemProperties):
    """
    Properties of a short-term storage system read from the configuration files.

    All aliases match the name of the corresponding field in the INI files.
    """

    def get_id(self) -> str:
        return transform_name_to_id(self.name)

    group: STStorageGroup = Field(
        STStorageGroup.OTHER1,
        description="Energy storage system group",
        title="Short-Term Storage Group",
    )
    injection_nominal_capacity: float = Field(
        0,
        description="Injection nominal capacity (MW)",
        ge=0,
        alias="injectionnominalcapacity",
        title="Injection Nominal Capacity",
    )
    withdrawal_nominal_capacity: float = Field(
        0,
        description="Withdrawal nominal capacity (MW)",
        ge=0,
        alias="withdrawalnominalcapacity",
        title="Withdrawal Nominal Capacity",
    )
    reservoir_capacity: float = Field(
        0,
        description="Reservoir capacity (MWh)",
        ge=0,
        alias="reservoircapacity",
        title="Reservoir Capacity",
    )
    efficiency: float = Field(
        1,
        description="Efficiency of the storage system (%)",
        ge=0,
        le=1,
        title="Efficiency",
    )
    # The `initial_level` value must be between 0 and 1, but the default value is 0.5
    initial_level: float = Field(
        0.5,
        description="Initial level of the storage system (%)",
        ge=0,
        le=1,
        alias="initiallevel",
        title="Initial Level",
    )
    initial_level_optim: bool = Field(
        False,
        description="Flag indicating if the initial level is optimized",
        alias="initialleveloptim",
        title="Initial Level Optimization",
    )


class STStorage880Properties(STStorageProperties):
    """
    Short term storage configuration model for 880 study.
    """

    # Activity status:
    # - True: the plant may generate.
    # - False: Ignored by the simulator.
    enabled: bool = Field(default=True, description="Activity status")


# noinspection SpellCheckingInspection
class STStorageConfig(STStorageProperties, LowerCaseIdentifier):
    """
    Manage the configuration files in the context of Short-Term Storage.
    It provides a convenient way to read and write configuration data from/to an INI file format.

    Usage:

    >>> from antarest.study.storage.rawstudy.model.filesystem.config.st_storage import STStorageConfig

    >>> st = STStorageConfig(name="Storage 1", group="battery", injection_nominal_capacity=1500)
    >>> st.id
    'storage 1'
    >>> st.group == STStorageGroup.BATTERY
    True
    >>> st.injection_nominal_capacity
    1500.0
    >>> st.injection_nominal_capacity = -897.32
    Traceback (most recent call last):
      ...
    pydantic.error_wrappers.ValidationError: 1 validation error for STStorageConfig
    injection_nominal_capacity
      ensure this value is greater than or equal to 0 (type=value_error.number.not_ge; limit_value=0)
    """


class STStorage880Config(STStorage880Properties, LowerCaseIdentifier):
    """
    Short Term Storage properties for study in version 8.8 or above.

    Usage:

    >>> from antarest.study.storage.rawstudy.model.filesystem.config.st_storage import STStorage880Config

    >>> st = STStorage880Config(name="Storage 1", group="battery", enabled=False)
    >>> st.id
    'storage 1'
    >>> st.group == STStorageGroup.BATTERY
    True
    >>> st.enabled
    False
    """


# NOTE: In the following Union, it is important to place the older version first,
# because otherwise, creating a short term storage always creates a v8.8 one.
STStorageConfigType = STStorageConfig | STStorage880Config
STStoragePropertiesType = STStorageProperties | STStorage880Properties


def create_st_storage_properties(study_version: StudyVersion, data: Dict[str, Any]) -> STStoragePropertiesType:
    """
    Factory method to create st_storage properties.

    Args:
        study_version: The version of the study.
        data: The dictionary of data to be used to initialize the model.

    Returns:
        The short term storage properties.

    Raises:
        ValueError: If the study version is not supported.
    """
    if study_version >= STUDY_VERSION_8_8:
        return STStorage880Properties.model_validate(data)
    elif study_version >= STUDY_VERSION_8_6:
        return STStorageProperties.model_validate(data)
    raise ValueError(f"Unsupported study version: {study_version}")


def get_st_storage_config_cls(study_version: StudyVersion) -> t.Type[STStorageConfigType]:
    """
    Retrieves the short-term storage configuration class based on the study version.

    Args:
        study_version: The version of the study.

    Returns:
        The short-term storage configuration class.
    """
    if study_version >= STUDY_VERSION_8_8:
        return STStorage880Config
    elif study_version >= STUDY_VERSION_8_6:
        return STStorageConfig
    raise ValueError(f"Unsupported study version: {study_version}")


def create_st_storage_config(study_version: StudyVersion, **kwargs: t.Any) -> STStorageConfigType:
    """
    Factory method to create a short-term storage configuration model.

    Args:
        study_version: The version of the study.
        **kwargs: The properties to be used to initialize the model.

    Returns:
        The short-term storage configuration model.

    Raises:
        ValueError: If the study version is not supported.
    """
    cls = get_st_storage_config_cls(study_version)
    return cls(**kwargs)
