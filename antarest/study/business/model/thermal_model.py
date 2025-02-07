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
from typing import Annotated

from antares.study.version import StudyVersion
from pydantic import Field
from typing_extensions import override

from antarest.core.serialization import AntaresBaseModel
from antarest.study.business.all_optional_meta import camel_case_model
from antarest.study.business.enum_ignore_case import EnumIgnoreCase


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

    @override
    def __repr__(self) -> str:  # pragma: no cover
        return f"{self.__class__.__name__}.{self.name}"


class LawOption(EnumIgnoreCase):
    """
    Law options used for series generation.
    The UNIFORM `law` is used by default.
    """

    UNIFORM = "uniform"
    GEOMETRIC = "geometric"

    @override
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

    @override
    def __repr__(self) -> str:  # pragma: no cover
        return f"{self.__class__.__name__}.{self.name}"

    @classmethod
    @override
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


# Annotated types useful for thermal cluster models

ClusterEnabled = Annotated[bool, Field(description="Activity status", title="Enabled")]

DEFAULT_ENABLED = True

# noinspection SpellCheckingInspection
ClusterUnitCount = Annotated[
    int,
    Field(
        ge=1,
        description="Unit count",
        alias="unitcount",
        title="Unit Count",
    ),
]

DEFAULT_UNIT_COUNT = 1


# noinspection SpellCheckingInspection
ClusterNominalCapacity = Annotated[
    float,
    Field(
        ge=0,
        description="Nominal capacity (MW per unit)",
        alias="nominalcapacity",
        title="Nominal Capacity",
    ),
]

DEFAULT_NOMINAL_CAPACITY = 0.0

ThermalClusterGroupField = Annotated[
    ThermalClusterGroup,
    Field(
        description="Thermal Cluster Group",
        title="Thermal Cluster Group",
    ),
]

DEFAULT_CLUSTER_GROUP = ThermalClusterGroup.OTHER1

LocalTSGenerationBehaviorField = Annotated[
    LocalTSGenerationBehavior,
    Field(
        description="Time Series Generation Option",
        alias="gen-ts",
        title="Time Series Generation",
    ),
]

DEFAUT_TS_GENERATION_BEHAVIOR = LocalTSGenerationBehavior.USE_GLOBAL

MinStablePower = Annotated[
    float,
    Field(
        description="Min. Stable Power (MW)",
        alias="min-stable-power",
        title="Min. Stable Power",
    ),
]

DEFAULT_MIN_STABLE_POWER = 0.0


MinUpTime = Annotated[
    int,
    Field(
        ge=1,
        le=168,
        description="Min. Up time (h)",
        alias="min-up-time",
        title="Min. Up Time",
    ),
]

DEFAULT_MIN_UP_TIME = 1


MinDownTime = Annotated[
    int,
    Field(
        ge=1,
        le=168,
        description="Min. Down time (h)",
        alias="min-down-time",
        title="Min. Down Time",
    ),
]

DEFAULT_MIN_DOWN_TIME = 1

MustRun = Annotated[
    bool,
    Field(
        description="Must run flag",
        alias="must-run",
        title="Must Run",
    ),
]

DEFAULT_MUST_RUN = False

Spinning = Annotated[
    float,
    Field(
        default=0.0,
        ge=0,
        le=100,
        description="Spinning (%)",
        title="Spinning",
    ),
]

DEFAULT_SPINNING = 0.0

VolatilityForced = Annotated[
    float,
    Field(
        ge=0,
        le=1,
        description="Forced Volatility",
        alias="volatility.forced",
        title="Forced Volatility",
    ),
]

VolatilityPlanned = Annotated[
    float,
    Field(
        ge=0,
        le=1,
        description="Planned volatility",
        alias="volatility.planned",
        title="Planned Volatility",
    ),
]

DEFAULT_VOLATILITY = 0.0

LawForced = Annotated[
    LawOption,
    Field(
        description="Forced Law (ts-generator)",
        alias="law.forced",
        title="Forced Law",
    ),
]

LawPlanned = Annotated[
    LawOption,
    Field(
        description="Planned Law (ts-generator)",
        alias="law.planned",
        title="Planned Law",
    ),
]

DEFAULT_LAW = LawOption.UNIFORM

MarginalCost = Annotated[
    float,
    Field(
        ge=0,
        description="Marginal cost (euros/MWh)",
        alias="marginal-cost",
        title="Marginal Cost",
    ),
]

DEFAULT_MARGINAL_COST = 0.0

SpreadCost = Annotated[
    float,
    Field(
        ge=0,
        description="Spread (euros/MWh)",
        alias="spread-cost",
        title="Spread Cost",
    ),
]

DEFAULT_SPREAD_COST = 0.0


FixedCost = Annotated[
    float,
    Field(
        ge=0,
        description="Fixed cost (euros/hour)",
        alias="fixed-cost",
        title="Fixed Cost",
    ),
]

DEFAULT_FIXED_COST = 0.0


StartupCost = Annotated[
    float,
    Field(
        ge=0,
        description="Startup cost (euros/startup)",
        alias="startup-cost",
        title="Startup Cost",
    ),
]

DEFAULT_STARTUP_COST = 0.0


MarketBidCost = Annotated[
    float,
    Field(
        ge=0,
        description="Market bid cost (euros/MWh)",
        alias="market-bid-cost",
        title="Market Bid Cost",
    ),
]

DEFAULT_MARKET_BID_COST = 0.0


DEFAULT_EMISSIONS = 0.0

Co2 = Annotated[
    float,
    Field(
        ge=0,
        description="Emission rate of CO2 (t/MWh)",
        title="Emission rate of CO2",
    ),
]

Nh3 = Annotated[
    float,
    Field(
        ge=0,
        description="Emission rate of NH3 (t/MWh)",
        title="Emission rate of NH3",
    ),
]

So2 = Annotated[
    float,
    Field(
        ge=0,
        description="Emission rate of SO2 (t/MWh)",
        title="Emission rate of SO2",
    ),
]

Nox = Annotated[
    float,
    Field(
        ge=0,
        description="Emission rate of NOX (t/MWh)",
        title="Emission rate of NOX",
    ),
]

Pm2_5 = Annotated[
    float,
    Field(
        ge=0,
        description="Emission rate of PM 2.5 (t/MWh)",
        title="Emission rate of PM 2.5",
        alias="pm2_5",
    ),
]

Pm5 = Annotated[
    float,
    Field(
        ge=0,
        description="Emission rate of PM 5 (t/MWh)",
        title="Emission rate of PM 5",
    ),
]

Pm10 = Annotated[
    float,
    Field(
        ge=0,
        description="Emission rate of PM 10 (t/MWh)",
        title="Emission rate of PM 10",
    ),
]

Nmvoc = Annotated[
    float,
    Field(
        ge=0,
        description="Emission rate of NMVOC (t/MWh)",
        title="Emission rate of NMVOC",
    ),
]

Op1 = Annotated[
    float,
    Field(
        ge=0,
        description="Emission rate of pollutant 1 (t/MWh)",
        title="Emission rate of pollutant 1",
    ),
]

Op2 = Annotated[
    float,
    Field(
        ge=0,
        description="Emission rate of pollutant 2 (t/MWh)",
        title="Emission rate of pollutant 2",
    ),
]

Op3 = Annotated[
    float,
    Field(
        ge=0,
        description="Emission rate of pollutant 3 (t/MWh)",
        title="Emission rate of pollutant 3",
    ),
]

Op4 = Annotated[
    float,
    Field(
        ge=0,
        description="Emission rate of pollutant 4 (t/MWh)",
        title="Emission rate of pollutant 4",
    ),
]

Op5 = Annotated[
    float,
    Field(
        ge=0,
        description="Emission rate of pollutant 5 (t/MWh)",
        title="Emission rate of pollutant 5",
    ),
]

ThermalCostGenerationField = Annotated[
    ThermalCostGeneration,
    Field(
        alias="costgeneration",
        description="Cost generation option",
        title="Cost Generation",
    ),
]

DEFAULT_COST_GENERATION = ThermalCostGeneration.SET_MANUALLY

Efficiency = Annotated[
    float,
    Field(
        ge=0,
        le=100,
        description="Efficiency (%)",
        title="Efficiency",
    ),
]

DEFAULT_EFFICIENCY: float = 100.0


# Even if `variableomcost` is a cost it could be negative.
VariableOMCost = Annotated[
    float,
    Field(
        description="Operating and Maintenance Cost (€/MWh)",
        alias="variableomcost",
        title="Variable O&M Cost",
    ),
]

DEFAULT_VARIABLE_OM_COST = 0.0


class ThermalProperties(AntaresBaseModel):
    """
    Thermal cluster configuration model.
    This model describes the configuration parameters for a thermal cluster.
    """

    name: str
    unit_count: ClusterUnitCount = DEFAULT_UNIT_COUNT
    nominal_capacity: ClusterNominalCapacity = DEFAULT_NOMINAL_CAPACITY
    enabled: ClusterEnabled = DEFAULT_ENABLED
    group: ThermalClusterGroupField = DEFAULT_CLUSTER_GROUP
    gen_ts: LocalTSGenerationBehaviorField = DEFAUT_TS_GENERATION_BEHAVIOR
    min_stable_power: MinStablePower = DEFAULT_MIN_STABLE_POWER
    min_up_time: MinUpTime = DEFAULT_MIN_UP_TIME
    min_down_time: MinDownTime = DEFAULT_MIN_DOWN_TIME
    must_run: MustRun = DEFAULT_MUST_RUN
    spinning: Spinning = DEFAULT_SPINNING
    volatility_forced: VolatilityForced = DEFAULT_VOLATILITY
    volatility_planned: VolatilityPlanned = DEFAULT_VOLATILITY
    law_forced: LawForced = DEFAULT_LAW
    law_planned: LawPlanned = DEFAULT_LAW
    marginal_cost: MarginalCost = DEFAULT_MARGINAL_COST
    spread_cost: SpreadCost = DEFAULT_SPREAD_COST
    fixed_cost: FixedCost = DEFAULT_FIXED_COST
    startup_cost: StartupCost = DEFAULT_STARTUP_COST
    market_bid_cost: MarketBidCost = DEFAULT_MARKET_BID_COST
    co2: Co2 = DEFAULT_EMISSIONS


class Thermal860Properties(ThermalProperties):
    """
    Thermal cluster configuration model for 860 study.
    """

    nh3: Nh3 = DEFAULT_EMISSIONS
    so2: So2 = DEFAULT_EMISSIONS
    nox: Nox = DEFAULT_EMISSIONS
    pm2_5: Pm2_5 = DEFAULT_EMISSIONS
    pm5: Pm5 = DEFAULT_EMISSIONS
    pm10: Pm10 = DEFAULT_EMISSIONS
    nmvoc: Nmvoc = DEFAULT_EMISSIONS
    op1: Op1 = DEFAULT_EMISSIONS
    op2: Op2 = DEFAULT_EMISSIONS
    op3: Op3 = DEFAULT_EMISSIONS
    op4: Op4 = DEFAULT_EMISSIONS
    op5: Op5 = DEFAULT_EMISSIONS


class Thermal870Properties(Thermal860Properties):
    """
    Thermal cluster configuration model for study in version 8.7 or above.
    """

    cost_generation: ThermalCostGenerationField = DEFAULT_COST_GENERATION
    efficiency: Efficiency = DEFAULT_EFFICIENCY
    variable_o_m_cost: VariableOMCost = DEFAULT_VARIABLE_OM_COST


class ThermalConfig(AntaresBaseModel):
    """
    Thermal properties with section ID.

    """

    id: str
    name: str
    unit_count: ClusterUnitCount = DEFAULT_UNIT_COUNT
    nominal_capacity: ClusterNominalCapacity = DEFAULT_NOMINAL_CAPACITY
    enabled: ClusterEnabled = DEFAULT_ENABLED
    group: ThermalClusterGroupField = DEFAULT_CLUSTER_GROUP
    gen_ts: LocalTSGenerationBehaviorField = DEFAUT_TS_GENERATION_BEHAVIOR
    min_stable_power: MinStablePower = DEFAULT_MIN_STABLE_POWER
    min_up_time: MinUpTime = DEFAULT_MIN_UP_TIME
    min_down_time: MinDownTime = DEFAULT_MIN_DOWN_TIME
    must_run: MustRun = DEFAULT_MUST_RUN
    spinning: Spinning = DEFAULT_SPINNING
    volatility_forced: VolatilityForced = DEFAULT_VOLATILITY
    volatility_planned: VolatilityPlanned = DEFAULT_VOLATILITY
    law_forced: LawForced = DEFAULT_LAW
    law_planned: LawPlanned = DEFAULT_LAW
    marginal_cost: MarginalCost = DEFAULT_MARGINAL_COST
    spread_cost: SpreadCost = DEFAULT_SPREAD_COST
    fixed_cost: FixedCost = DEFAULT_FIXED_COST
    startup_cost: StartupCost = DEFAULT_STARTUP_COST
    market_bid_cost: MarketBidCost = DEFAULT_MARKET_BID_COST
    co2: Co2 = DEFAULT_EMISSIONS


class Thermal860Config(ThermalConfig):
    nh3: Nh3 = DEFAULT_EMISSIONS
    so2: So2 = DEFAULT_EMISSIONS
    nox: Nox = DEFAULT_EMISSIONS
    pm2_5: Pm2_5 = DEFAULT_EMISSIONS
    pm5: Pm5 = DEFAULT_EMISSIONS
    pm10: Pm10 = DEFAULT_EMISSIONS
    nmvoc: Nmvoc = DEFAULT_EMISSIONS
    op1: Op1 = DEFAULT_EMISSIONS
    op2: Op2 = DEFAULT_EMISSIONS
    op3: Op3 = DEFAULT_EMISSIONS
    op4: Op4 = DEFAULT_EMISSIONS
    op5: Op5 = DEFAULT_EMISSIONS


class Thermal870Config(Thermal860Config):
    cost_generation: ThermalCostGenerationField = DEFAULT_COST_GENERATION
    efficiency: Efficiency = DEFAULT_EFFICIENCY
    variable_o_m_cost: VariableOMCost = DEFAULT_VARIABLE_OM_COST


ThermalConfigType = t.Union[Thermal870Config, Thermal860Config, ThermalConfig]


@camel_case_model
class ThermalClusterInput(AntaresBaseModel):
    class Config:
        @staticmethod
        def json_schema_extra(schema: t.MutableMapping[str, t.Any]) -> None:
            schema["example"] = ThermalClusterInput(
                group="Gas",
                name="Gas Cluster XY",
                enabled=False,
                unit_count=100,
                nominal_capacity=1000.0,
                gen_ts="use global",
                co2=7.0,
            ).model_dump(mode="json")

    name: str
    unit_count: t.Optional[ClusterUnitCount] = None
    nominal_capacity: t.Optional[ClusterNominalCapacity] = None
    enabled: t.Optional[ClusterEnabled] = None
    group: t.Optional[ThermalClusterGroupField] = None
    gen_ts: t.Optional[LocalTSGenerationBehaviorField] = None
    min_stable_power: t.Optional[MinStablePower] = None
    min_up_time: t.Optional[MinUpTime] = None
    min_down_time: t.Optional[MinDownTime] = None
    must_run: t.Optional[MustRun] = None
    spinning: t.Optional[Spinning] = None
    volatility_forced: t.Optional[VolatilityForced] = None
    volatility_planned: t.Optional[VolatilityPlanned] = None
    law_forced: t.Optional[LawForced] = None
    law_planned: t.Optional[LawPlanned] = None
    marginal_cost: t.Optional[MarginalCost] = None
    spread_cost: t.Optional[SpreadCost] = None
    fixed_cost: t.Optional[FixedCost] = None
    startup_cost: t.Optional[StartupCost] = None
    market_bid_cost: t.Optional[MarketBidCost] = None
    co2: t.Optional[Co2] = None
    nh3: t.Optional[Nh3] = None
    so2: t.Optional[So2] = None
    nox: t.Optional[Nox] = None
    pm2_5: t.Optional[Pm2_5] = None
    pm5: t.Optional[Pm5] = None
    pm10: t.Optional[Pm10] = None
    nmvoc: t.Optional[Nmvoc] = None
    op1: t.Optional[Op1] = None
    op2: t.Optional[Op2] = None
    op3: t.Optional[Op3] = None
    op4: t.Optional[Op4] = None
    op5: t.Optional[Op5] = None
    cost_generation: t.Optional[ThermalCostGenerationField] = None
    efficiency: t.Optional[Efficiency] = None
    variable_o_m_cost: t.Optional[VariableOMCost] = None


def get_thermal_config_cls(study_version: StudyVersion) -> t.Type[ThermalConfigType]:
    """
    Retrieves the thermal configuration class based on the study version.

    Args:
        study_version: The version of the study.

    Returns:
        The thermal configuration class.
    """
    if study_version >= 870:
        return Thermal870Config
    elif study_version == 860:
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
