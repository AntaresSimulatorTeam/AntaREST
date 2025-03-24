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
from typing import Annotated, Any, TypeVar

from antares.study.version import StudyVersion
from pydantic import ConfigDict, Field, field_validator, model_validator
from pydantic.alias_generators import to_camel
from pydantic_core.core_schema import ValidationInfo
from typing_extensions import override

from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.string import to_kebab_case
from antarest.study.business.enum_ignore_case import EnumIgnoreCase
from antarest.study.model import STUDY_VERSION_8_6, STUDY_VERSION_8_7
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.config.validation import (
    ItemName,
    extract_version,
    study_version_context,
)


def validate_min_version(min_version: StudyVersion, default_value: Any, data: Any, info: ValidationInfo) -> Any:
    study_version = extract_version(info)
    if study_version < min_version:
        if data is not None:
            raise ValueError(f"Field {info.field_name} is not a valid field for study version {study_version}")
        return None
    if data is None:
        return default_value
    else:
        return data


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

    NUCLEAR = "nuclear"
    LIGNITE = "lignite"
    HARD_COAL = "hard Coal"
    GAS = "gas"
    OIL = "oil"
    MIXED_FUEL = "mixed fuel"
    OTHER1 = "other 1"
    OTHER2 = "other 2"
    OTHER3 = "other 3"
    OTHER4 = "other 4"

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


class ThermalClusterFileData(AntaresBaseModel):
    """
    Thermal cluster data parsed from INI file.

    TODO SL: should be in a DAO layer, not with business models
    """

    model_config = ConfigDict(alias_generator=to_kebab_case, extra="forbid", populate_by_name=True)

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
    co2: float = Field(default=DEFAULT_EMISSIONS, ge=0)

    # Added in 8.6
    nh3: t.Optional[float] = Field(default=None, ge=0, validate_default=True)
    so2: t.Optional[float] = Field(default=None, ge=0, validate_default=True)
    nox: t.Optional[float] = Field(default=None, ge=0, validate_default=True)
    pm2_5: t.Optional[float] = Field(default=None, ge=0, validate_default=True, alias="pm2_5")
    pm5: t.Optional[float] = Field(default=None, ge=0, validate_default=True)
    pm10: t.Optional[float] = Field(default=None, ge=0, validate_default=True)
    nmvoc: t.Optional[float] = Field(default=None, ge=0, validate_default=True)
    op1: t.Optional[float] = Field(default=None, ge=0, validate_default=True)
    op2: t.Optional[float] = Field(default=None, ge=0, validate_default=True)
    op3: t.Optional[float] = Field(default=None, ge=0, validate_default=True)
    op4: t.Optional[float] = Field(default=None, ge=0, validate_default=True)
    op5: t.Optional[float] = Field(default=None, ge=0, validate_default=True)

    # Added in 8.7
    cost_generation: t.Optional[ThermalCostGeneration] = Field(
        default=None, validate_default=True, alias="costgeneration"
    )
    efficiency: t.Optional[float] = Field(default=None, ge=0, validate_default=True)
    variable_o_m_cost: t.Optional[float] = Field(default=None, ge=0, validate_default=True, alias="variableomcost")

    @field_validator(
        "nh3", "so2", "nox", "pm2_5", "pm5", "pm10", "nmvoc", "op1", "op2", "op3", "op4", "op5", mode="before"
    )
    @classmethod
    def validate_8_6_emissions(cls, data: Any, info: ValidationInfo) -> Any:
        return validate_min_version(min_version=STUDY_VERSION_8_6, default_value=0, data=data, info=info)

    @field_validator("cost_generation", mode="before")
    @classmethod
    def validate_8_7_cost_generation(cls, data: Any, info: ValidationInfo) -> Any:
        return validate_min_version(
            min_version=STUDY_VERSION_8_7, default_value=ThermalCostGeneration.SET_MANUALLY, data=data, info=info
        )

    @field_validator("efficiency", mode="before")
    @classmethod
    def validate_8_7_efficiency(cls, data: Any, info: ValidationInfo) -> Any:
        return validate_min_version(min_version=STUDY_VERSION_8_7, default_value=100, data=data, info=info)

    @field_validator("variable_o_m_cost", mode="before")
    @classmethod
    def validate_8_7_variable_o_m_cost(cls, data: Any, info: ValidationInfo) -> Any:
        return validate_min_version(min_version=STUDY_VERSION_8_7, default_value=0, data=data, info=info)

    def to_model(self) -> "ThermalCluster":
        return ThermalCluster.model_validate(self.model_dump())

    @classmethod
    def from_model(cls, study_version: StudyVersion, cluster: "ThermalCluster") -> "ThermalClusterFileData":
        return cls.model_validate(cluster.model_dump(exclude={"id"}), context=study_version_context(study_version))


class ThermalCluster(AntaresBaseModel):
    """
    Thermal cluster model.

    TODO SL: wed'better have some validation here too, indeed
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
    name: str
    unit_count: int = DEFAULT_UNIT_COUNT
    nominal_capacity: float = DEFAULT_NOMINAL_CAPACITY
    enabled: bool = DEFAULT_ENABLED
    group: ThermalClusterGroup = DEFAULT_CLUSTER_GROUP
    gen_ts: LocalTSGenerationBehavior = DEFAUT_TS_GENERATION_BEHAVIOR
    min_stable_power: float = DEFAULT_MIN_STABLE_POWER
    min_up_time: int = DEFAULT_MIN_UP_TIME
    min_down_time: int = DEFAULT_MIN_DOWN_TIME
    must_run: bool = DEFAULT_MUST_RUN
    spinning: float = DEFAULT_SPINNING
    volatility_forced: float = DEFAULT_VOLATILITY
    volatility_planned: float = DEFAULT_VOLATILITY
    law_forced: LawOption = DEFAULT_LAW
    law_planned: LawOption = DEFAULT_LAW
    marginal_cost: float = DEFAULT_MARGINAL_COST
    spread_cost: float = DEFAULT_SPREAD_COST
    fixed_cost: float = DEFAULT_FIXED_COST
    startup_cost: float = DEFAULT_STARTUP_COST
    market_bid_cost: float = DEFAULT_MARKET_BID_COST
    co2: float = Field(default=0, ge=0)

    # Added in 8.6
    nh3: t.Optional[float] = Field(default=None, ge=0)
    so2: t.Optional[float] = Field(default=None, ge=0)
    nox: t.Optional[float] = Field(default=None, ge=0)
    pm2_5: t.Optional[float] = Field(default=None, ge=0)
    pm5: t.Optional[float] = Field(default=None, ge=0)
    pm10: t.Optional[float] = Field(default=None, ge=0)
    nmvoc: t.Optional[float] = Field(default=None, ge=0)
    op1: t.Optional[float] = Field(default=None, ge=0)
    op2: t.Optional[float] = Field(default=None, ge=0)
    op3: t.Optional[float] = Field(default=None, ge=0)
    op4: t.Optional[float] = Field(default=None, ge=0)
    op5: t.Optional[float] = Field(default=None, ge=0)

    # Added in 8.7
    cost_generation: t.Optional[ThermalCostGeneration] = Field(default=None)
    efficiency: t.Optional[float] = Field(default=None, ge=0)
    variable_o_m_cost: t.Optional[float] = Field(default=None, ge=0)


def parse_thermal_cluster(study_version: StudyVersion, data: Any) -> ThermalCluster:
    return ThermalClusterFileData.model_validate(data, context=study_version_context(study_version)).to_model()


def serialize_thermal_cluster(study_version: StudyVersion, cluster: ThermalCluster) -> dict[str, Any]:
    return ThermalClusterFileData.from_model(study_version, cluster).model_dump(by_alias=True, exclude_none=True)


T = TypeVar("T")


class ThermalClusterCreation(AntaresBaseModel):
    class Config:
        alias_generator = to_camel
        extra = "forbid"
        populate_by_name = True

        @staticmethod
        def json_schema_extra(schema: t.MutableMapping[str, t.Any]) -> None:
            schema["example"] = ThermalClusterCreation(
                group="Gas",
                name="Gas Cluster XY",
                enabled=False,
                unit_count=100,
                nominal_capacity=1000.0,
                gen_ts="use global",
                co2=7.0,
            ).model_dump(mode="json")

    name: ItemName
    unit_count: t.Optional[int] = None
    nominal_capacity: t.Optional[float] = None
    enabled: t.Optional[bool] = None
    group: t.Optional[ThermalClusterGroup] = None
    gen_ts: t.Optional[LocalTSGenerationBehavior] = None
    min_stable_power: t.Optional[float] = None
    min_up_time: t.Optional[int] = None
    min_down_time: t.Optional[int] = None
    must_run: t.Optional[bool] = None
    spinning: t.Optional[float] = None
    volatility_forced: t.Optional[float] = None
    volatility_planned: t.Optional[float] = None
    law_forced: t.Optional[LawOption] = None
    law_planned: t.Optional[LawOption] = None
    marginal_cost: t.Optional[float] = None
    spread_cost: t.Optional[float] = None
    fixed_cost: t.Optional[float] = None
    startup_cost: t.Optional[float] = None
    market_bid_cost: t.Optional[float] = None
    co2: t.Optional[float] = None
    nh3: t.Optional[float] = None
    so2: t.Optional[float] = None
    nox: t.Optional[float] = None
    pm2_5: t.Optional[float] = None
    pm5: t.Optional[float] = None
    pm10: t.Optional[float] = None
    nmvoc: t.Optional[float] = None
    op1: t.Optional[float] = None
    op2: t.Optional[float] = None
    op3: t.Optional[float] = None
    op4: t.Optional[float] = None
    op5: t.Optional[float] = None
    cost_generation: t.Optional[ThermalCostGeneration] = None
    efficiency: t.Optional[float] = None
    variable_o_m_cost: t.Optional[float] = None

    @classmethod
    def from_cluster(cls, cluster: ThermalCluster) -> "ThermalClusterCreation":
        return ThermalClusterCreation.model_validate(cluster.model_dump(mode="json", exclude={"id"}, exclude_none=True))


class ThermalClusterUpdate(AntaresBaseModel):
    class Config:
        alias_generator = to_camel
        extra = "forbid"
        populate_by_name = True

        @staticmethod
        def json_schema_extra(schema: t.MutableMapping[str, t.Any]) -> None:
            schema["example"] = ThermalClusterUpdate(
                group="Gas",
                name="Gas Cluster XY",
                enabled=False,
                unit_count=100,
                nominal_capacity=1000.0,
                gen_ts="use global",
                co2=7.0,
            ).model_dump(mode="json")

    name: t.Optional[str] = None  # TODO SL: better ignore this, not handled correctly
    unit_count: t.Optional[int] = Field(ge=1, default=None)  # TODO SL: generalize validation of that object
    nominal_capacity: t.Optional[float] = None
    enabled: t.Optional[bool] = None
    group: t.Optional[ThermalClusterGroup] = None
    gen_ts: t.Optional[LocalTSGenerationBehavior] = None
    min_stable_power: t.Optional[float] = None
    min_up_time: t.Optional[int] = None
    min_down_time: t.Optional[int] = None
    must_run: t.Optional[bool] = None
    spinning: t.Optional[float] = None
    volatility_forced: t.Optional[float] = None
    volatility_planned: t.Optional[float] = None
    law_forced: t.Optional[LawOption] = None
    law_planned: t.Optional[LawOption] = None
    marginal_cost: t.Optional[float] = None
    spread_cost: t.Optional[float] = None
    fixed_cost: t.Optional[float] = None
    startup_cost: t.Optional[float] = None
    market_bid_cost: t.Optional[float] = None
    co2: t.Optional[float] = None
    nh3: t.Optional[float] = None
    so2: t.Optional[float] = None
    nox: t.Optional[float] = None
    pm2_5: t.Optional[float] = None
    pm5: t.Optional[float] = None
    pm10: t.Optional[float] = None
    nmvoc: t.Optional[float] = None
    op1: t.Optional[float] = None
    op2: t.Optional[float] = None
    op3: t.Optional[float] = None
    op4: t.Optional[float] = None
    op5: t.Optional[float] = None
    cost_generation: t.Optional[ThermalCostGeneration] = None
    efficiency: t.Optional[float] = None
    variable_o_m_cost: t.Optional[float] = None
