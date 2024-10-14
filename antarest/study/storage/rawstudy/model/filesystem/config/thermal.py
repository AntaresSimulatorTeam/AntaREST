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
from antarest.study.model import STUDY_VERSION_8_6, STUDY_VERSION_8_7
from antarest.study.storage.rawstudy.model.filesystem.config.cluster import ClusterProperties
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import IgnoreCaseIdentifier


class LocalTSGenerationBehavior(EnumIgnoreCase):
    """
    Options related to time series generation.
    The option `USE_GLOBAL` is used by default.

    Attributes:
        USE_GLOBAL: Use the global time series parameters.
        FORCE_NO_GENERATION: Do not generate time series.
        FORCE_GENERATION: Force the generation of time series.
    """

    USE_GLOBAL = "use global"
    FORCE_NO_GENERATION = "force no generation"
    FORCE_GENERATION = "force generation"

    def __repr__(self) -> str:  # pragma: no cover
        return f"{self.__class__.__name__}.{self.name}"


class LawOption(EnumIgnoreCase):
    """
    Law options used for series generation.
    The UNIFORM `law` is used by default.
    """

    UNIFORM = "uniform"
    GEOMETRIC = "geometric"

    def __repr__(self) -> str:  # pragma: no cover
        return f"{self.__class__.__name__}.{self.name}"


class ThermalClusterGroup(EnumIgnoreCase):
    """
    Thermal cluster groups.
    The group `OTHER1` is used by default.
    """

    NUCLEAR = "Nuclear"
    LIGNITE = "Lignite"
    HARD_COAL = "Hard Coal"
    GAS = "Gas"
    OIL = "Oil"
    MIXED_FUEL = "Mixed Fuel"
    OTHER1 = "Other 1"
    OTHER2 = "Other 2"
    OTHER3 = "Other 3"
    OTHER4 = "Other 4"

    def __repr__(self) -> str:  # pragma: no cover
        return f"{self.__class__.__name__}.{self.name}"

    @classmethod
    def _missing_(cls, value: object) -> t.Optional["ThermalClusterGroup"]:
        """
        Retrieves the default group or the matched group when an unknown value is encountered.
        """
        if isinstance(value, str):
            # Check if any group value matches the input value ignoring case sensitivity.
            # noinspection PyUnresolvedReferences
            if any(value.upper() == group.value.upper() for group in cls):
                return t.cast(ThermalClusterGroup, super()._missing_(value))
            # If a group is not found, return the default group ('OTHER1' by default).
            # Note that 'OTHER' is an alias for 'OTHER1'.
            return cls.OTHER1
        return t.cast(t.Optional["ThermalClusterGroup"], super()._missing_(value))


class ThermalCostGeneration(EnumIgnoreCase):
    """
    Specifies how to generate thermal cluster cost.
    The value `SetManually` is used by default.
    """

    SET_MANUALLY = "SetManually"
    USE_COST_TIME_SERIES = "useCostTimeseries"


class ThermalProperties(ClusterProperties):
    """
    Thermal cluster configuration model.
    This model describes the configuration parameters for a thermal cluster.
    """

    group: ThermalClusterGroup = Field(
        default=ThermalClusterGroup.OTHER1,
        description="Thermal Cluster Group",
        title="Thermal Cluster Group",
    )

    gen_ts: LocalTSGenerationBehavior = Field(
        default=LocalTSGenerationBehavior.USE_GLOBAL,
        description="Time Series Generation Option",
        alias="gen-ts",
        title="Time Series Generation",
    )
    min_stable_power: float = Field(
        default=0.0,
        description="Min. Stable Power (MW)",
        alias="min-stable-power",
        title="Min. Stable Power",
    )
    min_up_time: int = Field(
        default=1,
        ge=1,
        le=168,
        description="Min. Up time (h)",
        alias="min-up-time",
        title="Min. Up Time",
    )
    min_down_time: int = Field(
        default=1,
        ge=1,
        le=168,
        description="Min. Down time (h)",
        alias="min-down-time",
        title="Min. Down Time",
    )
    must_run: bool = Field(
        default=False,
        description="Must run flag",
        alias="must-run",
        title="Must Run",
    )
    spinning: float = Field(
        default=0.0,
        ge=0,
        le=100,
        description="Spinning (%)",
        title="Spinning",
    )
    volatility_forced: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description="Forced Volatility",
        alias="volatility.forced",
        title="Forced Volatility",
    )
    volatility_planned: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description="Planned volatility",
        alias="volatility.planned",
        title="Planned Volatility",
    )
    law_forced: LawOption = Field(
        default=LawOption.UNIFORM,
        description="Forced Law (ts-generator)",
        alias="law.forced",
        title="Forced Law",
    )
    law_planned: LawOption = Field(
        default=LawOption.UNIFORM,
        description="Planned Law (ts-generator)",
        alias="law.planned",
        title="Planned Law",
    )
    marginal_cost: float = Field(
        default=0.0,
        ge=0,
        description="Marginal cost (euros/MWh)",
        alias="marginal-cost",
        title="Marginal Cost",
    )
    spread_cost: float = Field(
        default=0.0,
        ge=0,
        description="Spread (euros/MWh)",
        alias="spread-cost",
        title="Spread Cost",
    )
    fixed_cost: float = Field(
        default=0.0,
        ge=0,
        description="Fixed cost (euros/hour)",
        alias="fixed-cost",
        title="Fixed Cost",
    )
    startup_cost: float = Field(
        default=0.0,
        ge=0,
        description="Startup cost (euros/startup)",
        alias="startup-cost",
        title="Startup Cost",
    )
    market_bid_cost: float = Field(
        default=0.0,
        ge=0,
        description="Market bid cost (euros/MWh)",
        alias="market-bid-cost",
        title="Market Bid Cost",
    )
    co2: float = Field(
        default=0.0,
        ge=0,
        description="Emission rate of CO2 (t/MWh)",
        title="Emission rate of CO2",
    )


class Thermal860Properties(ThermalProperties):
    """
    Thermal cluster configuration model for 860 study.
    """

    nh3: float = Field(
        default=0.0,
        ge=0,
        description="Emission rate of NH3 (t/MWh)",
        title="Emission rate of NH3",
    )
    so2: float = Field(
        default=0.0,
        ge=0,
        description="Emission rate of SO2 (t/MWh)",
        title="Emission rate of SO2",
    )
    nox: float = Field(
        default=0.0,
        ge=0,
        description="Emission rate of NOX (t/MWh)",
        title="Emission rate of NOX",
    )
    pm2_5: float = Field(
        default=0.0,
        ge=0,
        description="Emission rate of PM 2.5 (t/MWh)",
        title="Emission rate of PM 2.5",
        alias="pm2_5",
    )
    pm5: float = Field(
        default=0.0,
        ge=0,
        description="Emission rate of PM 5 (t/MWh)",
        title="Emission rate of PM 5",
    )
    pm10: float = Field(
        default=0.0,
        ge=0,
        description="Emission rate of PM 10 (t/MWh)",
        title="Emission rate of PM 10",
    )
    nmvoc: float = Field(
        default=0.0,
        ge=0,
        description="Emission rate of NMVOC (t/MWh)",
        title="Emission rate of NMVOC",
    )
    op1: float = Field(
        default=0.0,
        ge=0,
        description="Emission rate of pollutant 1 (t/MWh)",
        title="Emission rate of pollutant 1",
    )
    op2: float = Field(
        default=0.0,
        ge=0,
        description="Emission rate of pollutant 2 (t/MWh)",
        title="Emission rate of pollutant 2",
    )
    op3: float = Field(
        default=0.0,
        ge=0,
        description="Emission rate of pollutant 3 (t/MWh)",
        title="Emission rate of pollutant 3",
    )
    op4: float = Field(
        default=0.0,
        ge=0,
        description="Emission rate of pollutant 4 (t/MWh)",
        title="Emission rate of pollutant 4",
    )
    op5: float = Field(
        default=0.0,
        ge=0,
        description="Emission rate of pollutant 5 (t/MWh)",
        title="Emission rate of pollutant 5",
    )


# noinspection SpellCheckingInspection
class Thermal870Properties(Thermal860Properties):
    """
    Thermal cluster configuration model for study in version 8.7 or above.
    """

    cost_generation: ThermalCostGeneration = Field(
        default=ThermalCostGeneration.SET_MANUALLY,
        alias="costgeneration",
        description="Cost generation option",
        title="Cost Generation",
    )
    efficiency: float = Field(
        default=100.0,
        ge=0,
        le=100,
        description="Efficiency (%)",
        title="Efficiency",
    )
    # Even if `variableomcost` is a cost it could be negative.
    variable_o_m_cost: float = Field(
        default=0.0,
        description="Operating and Maintenance Cost (€/MWh)",
        alias="variableomcost",
        title="Variable O&M Cost",
    )


class ThermalConfig(ThermalProperties, IgnoreCaseIdentifier):
    """
    Thermal properties with section ID.

    Usage:

    >>> from antarest.study.storage.rawstudy.model.filesystem.config.thermal import ThermalConfig

    >>> cl = ThermalConfig(name="cluster 01!", group="Nuclear", co2=123)
    >>> cl.id
    'cluster 01'
    >>> cl.group == ThermalClusterGroup.NUCLEAR
    True
    >>> cl.co2
    123.0
    >>> cl.nh3
    Traceback (most recent call last):
      ...
    AttributeError: 'ThermalConfig' object has no attribute 'nh3'"""


class Thermal860Config(Thermal860Properties, IgnoreCaseIdentifier):
    """
    Thermal properties for study in version 860

    Usage:

    >>> from antarest.study.storage.rawstudy.model.filesystem.config.thermal import Thermal860Config

    >>> cl = Thermal860Config(name="cluster 01!", group="Nuclear", co2=123, nh3=456)
    >>> cl.id
    'cluster 01'
    >>> cl.group == ThermalClusterGroup.NUCLEAR
    True
    >>> cl.co2
    123.0
    >>> cl.nh3
    456.0
    >>> cl.op1
    0.0
    """


class Thermal870Config(Thermal870Properties, IgnoreCaseIdentifier):
    """
    Thermal properties for study in version 8.7 or above.

    Usage:

    >>> from antarest.study.storage.rawstudy.model.filesystem.config.thermal import Thermal870Config

    >>> cl = Thermal870Config(name="cluster 01!", group="Nuclear", co2=123, nh3=456, efficiency=97)
    >>> cl.id
    'cluster 01'
    >>> cl.group == ThermalClusterGroup.NUCLEAR
    True
    >>> cl.co2
    123.0
    >>> cl.nh3
    456.0
    >>> cl.op1
    0.0
    >>> cl.efficiency
    97.0
    >>> cl.variable_o_m_cost
    0.0
    >>> cl.cost_generation == ThermalCostGeneration.SET_MANUALLY
    True
    """


# NOTE: In the following Union, it is important to place the most specific type first,
# because the type matching generally occurs sequentially from left to right within the union.
ThermalConfigType = t.Union[Thermal870Config, Thermal860Config, ThermalConfig]


def get_thermal_config_cls(study_version: StudyVersion) -> t.Type[ThermalConfigType]:
    """
    Retrieves the thermal configuration class based on the study version.

    Args:
        study_version: The version of the study.

    Returns:
        The thermal configuration class.
    """
    if study_version >= STUDY_VERSION_8_7:
        return Thermal870Config
    elif study_version == STUDY_VERSION_8_6:
        return Thermal860Config
    else:
        return ThermalConfig


def create_thermal_config(study_version: StudyVersion, **kwargs: t.Any) -> ThermalConfigType:
    """
    Factory method to create a thermal configuration model.

    Args:
        study_version: The version of the study.
        **kwargs: The properties to be used to initialize the model.

    Returns:
        The thermal configuration model.

    Raises:
        ValueError: If the study version is not supported.
    """
    cls = get_thermal_config_cls(study_version)
    return cls.model_validate(kwargs)
