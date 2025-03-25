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
from typing import Any, MutableMapping, Optional, cast

from antares.study.version import StudyVersion
from pydantic import ConfigDict, Field, model_validator
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
    def _missing_(cls, value: object) -> Optional["ThermalClusterGroup"]:
        """
        Retrieves the default group or the matched group when an unknown value is encountered.
        """
        if isinstance(value, str):
            # Check if any group value matches the input value ignoring case sensitivity.
            # noinspection PyUnresolvedReferences
            if any(value.upper() == group.value.upper() for group in cls):
                return cast(ThermalClusterGroup, super()._missing_(value))
            # If a group is not found, return the default group ('OTHER1' by default).
            # Note that 'OTHER' is an alias for 'OTHER1'.
            return cls.OTHER1
        return cast(Optional["ThermalClusterGroup"], super()._missing_(value))


class ThermalCostGeneration(EnumIgnoreCase):
    """
    Specifies how to generate thermal cluster cost.
    The value `SetManually` is used by default.
    """

    SET_MANUALLY = "SetManually"
    USE_COST_TIME_SERIES = "useCostTimeseries"


class ThermalClusterFileData(AntaresBaseModel):
    """
    Thermal cluster data parsed from INI file.

    TODO SL: should be in a DAO layer, not with business models
    """

    model_config = ConfigDict(alias_generator=to_kebab_case, extra="forbid", populate_by_name=True)

    name: str
    unit_count: int = Field(default=1, ge=1, alias="unitcount")
    nominal_capacity: float = Field(default=0, ge=0, alias="nominalcapacity")
    enabled: bool = True
    group: ThermalClusterGroup = ThermalClusterGroup.OTHER1
    gen_ts: LocalTSGenerationBehavior = Field(default=LocalTSGenerationBehavior.USE_GLOBAL)
    min_stable_power: float = Field(default=0)
    min_up_time: int = Field(default=1, ge=1, le=168)
    min_down_time: int = Field(default=1, ge=1, le=168)
    must_run: bool = Field(default=False)
    spinning: float = Field(default=0, ge=0, le=100)
    volatility_forced: float = Field(default=0, ge=0, le=1, alias="volatility.forced")
    volatility_planned: float = Field(default=0, ge=0, le=1, alias="volatility.planned")
    law_forced: LawOption = Field(default=LawOption.UNIFORM, alias="law.forced")
    law_planned: LawOption = Field(default=LawOption.UNIFORM, alias="law.planned")
    marginal_cost: float = Field(default=0, ge=0)
    spread_cost: float = Field(default=0, ge=0)
    fixed_cost: float = Field(default=0, ge=0)
    startup_cost: float = Field(default=0, ge=0)
    market_bid_cost: float = Field(default=0, ge=0)
    co2: float = Field(default=0, ge=0)

    # Added in 8.6
    nh3: Optional[float] = Field(default=None, ge=0)
    so2: Optional[float] = Field(default=None, ge=0)
    nox: Optional[float] = Field(default=None, ge=0)
    pm2_5: Optional[float] = Field(default=None, ge=0, alias="pm2_5")
    pm5: Optional[float] = Field(default=None, ge=0)
    pm10: Optional[float] = Field(default=None, ge=0)
    nmvoc: Optional[float] = Field(default=None, ge=0)
    op1: Optional[float] = Field(default=None, ge=0)
    op2: Optional[float] = Field(default=None, ge=0)
    op3: Optional[float] = Field(default=None, ge=0)
    op4: Optional[float] = Field(default=None, ge=0)
    op5: Optional[float] = Field(default=None, ge=0)

    # Added in 8.7
    cost_generation: Optional[ThermalCostGeneration] = Field(default=None, alias="costgeneration")
    efficiency: Optional[float] = Field(default=None, ge=0)
    variable_o_m_cost: Optional[float] = Field(default=None, ge=0, alias="variableomcost")

    def to_model(self) -> "ThermalCluster":
        return ThermalCluster.model_validate(self.model_dump())

    @classmethod
    def from_model(cls, study_version: StudyVersion, cluster: "ThermalCluster") -> "ThermalClusterFileData":
        return cls.model_validate(cluster.model_dump(exclude={"id"}))


class ThermalCluster(AntaresBaseModel):
    """
    Thermal cluster model.
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
    unit_count: int = 1
    nominal_capacity: float = 0
    enabled: bool = True
    group: ThermalClusterGroup = ThermalClusterGroup.OTHER1
    gen_ts: LocalTSGenerationBehavior = LocalTSGenerationBehavior.USE_GLOBAL
    min_stable_power: float = 0
    min_up_time: int = 1
    min_down_time: int = 1
    must_run: bool = False
    spinning: float = 0
    volatility_forced: float = 0
    volatility_planned: float = 0
    law_forced: LawOption = LawOption.UNIFORM
    law_planned: LawOption = LawOption.UNIFORM
    marginal_cost: float = 0
    spread_cost: float = 0
    fixed_cost: float = 0
    startup_cost: float = 0
    market_bid_cost: float = 0
    co2: float = Field(default=0, ge=0)

    # Added in 8.6
    nh3: Optional[float] = Field(default=None, ge=0)
    so2: Optional[float] = Field(default=None, ge=0)
    nox: Optional[float] = Field(default=None, ge=0)
    pm2_5: Optional[float] = Field(default=None, ge=0)
    pm5: Optional[float] = Field(default=None, ge=0)
    pm10: Optional[float] = Field(default=None, ge=0)
    nmvoc: Optional[float] = Field(default=None, ge=0)
    op1: Optional[float] = Field(default=None, ge=0)
    op2: Optional[float] = Field(default=None, ge=0)
    op3: Optional[float] = Field(default=None, ge=0)
    op4: Optional[float] = Field(default=None, ge=0)
    op5: Optional[float] = Field(default=None, ge=0)

    # Added in 8.7
    cost_generation: Optional[ThermalCostGeneration] = Field(default=None)
    efficiency: Optional[float] = Field(default=None, ge=0)
    variable_o_m_cost: Optional[float] = Field(default=None, ge=0)


def parse_thermal_cluster(study_version: StudyVersion, data: Any) -> ThermalCluster:
    cluster = ThermalClusterFileData.model_validate(data).to_model()
    validate_against_version(study_version, cluster)
    return cluster


def serialize_thermal_cluster(study_version: StudyVersion, cluster: ThermalCluster) -> dict[str, Any]:
    return ThermalClusterFileData.from_model(study_version, cluster).model_dump(by_alias=True, exclude_none=True)


class ThermalClusterCreation(AntaresBaseModel):
    class Config:
        alias_generator = to_camel
        extra = "forbid"
        populate_by_name = True

        @staticmethod
        def json_schema_extra(schema: MutableMapping[str, Any]) -> None:
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
    unit_count: Optional[int] = None
    nominal_capacity: Optional[float] = None
    enabled: Optional[bool] = None
    group: Optional[ThermalClusterGroup] = None
    gen_ts: Optional[LocalTSGenerationBehavior] = None
    min_stable_power: Optional[float] = None
    min_up_time: Optional[int] = None
    min_down_time: Optional[int] = None
    must_run: Optional[bool] = None
    spinning: Optional[float] = None
    volatility_forced: Optional[float] = None
    volatility_planned: Optional[float] = None
    law_forced: Optional[LawOption] = None
    law_planned: Optional[LawOption] = None
    marginal_cost: Optional[float] = None
    spread_cost: Optional[float] = None
    fixed_cost: Optional[float] = None
    startup_cost: Optional[float] = None
    market_bid_cost: Optional[float] = None
    co2: Optional[float] = None
    nh3: Optional[float] = None
    so2: Optional[float] = None
    nox: Optional[float] = None
    pm2_5: Optional[float] = None
    pm5: Optional[float] = None
    pm10: Optional[float] = None
    nmvoc: Optional[float] = None
    op1: Optional[float] = None
    op2: Optional[float] = None
    op3: Optional[float] = None
    op4: Optional[float] = None
    op5: Optional[float] = None
    cost_generation: Optional[ThermalCostGeneration] = None
    efficiency: Optional[float] = None
    variable_o_m_cost: Optional[float] = None

    @classmethod
    def from_cluster(cls, cluster: ThermalCluster) -> "ThermalClusterCreation":
        return ThermalClusterCreation.model_validate(cluster.model_dump(mode="json", exclude={"id"}, exclude_none=True))


class ThermalClusterUpdate(AntaresBaseModel):
    class Config:
        alias_generator = to_camel
        extra = "forbid"
        populate_by_name = True

        @staticmethod
        def json_schema_extra(schema: MutableMapping[str, Any]) -> None:
            schema["example"] = ThermalClusterUpdate(
                group="Gas",
                name="Gas Cluster XY",
                enabled=False,
                unit_count=100,
                nominal_capacity=1000.0,
                gen_ts="use global",
                co2=7.0,
            ).model_dump(mode="json")

    name: Optional[str] = None  # TODO SL: better ignore this, not handled correctly
    unit_count: Optional[int] = Field(ge=1, default=None)  # TODO SL: generalize validation of that object
    nominal_capacity: Optional[float] = None
    enabled: Optional[bool] = None
    group: Optional[ThermalClusterGroup] = None
    gen_ts: Optional[LocalTSGenerationBehavior] = None
    min_stable_power: Optional[float] = None
    min_up_time: Optional[int] = None
    min_down_time: Optional[int] = None
    must_run: Optional[bool] = None
    spinning: Optional[float] = None
    volatility_forced: Optional[float] = None
    volatility_planned: Optional[float] = None
    law_forced: Optional[LawOption] = None
    law_planned: Optional[LawOption] = None
    marginal_cost: Optional[float] = None
    spread_cost: Optional[float] = None
    fixed_cost: Optional[float] = None
    startup_cost: Optional[float] = None
    market_bid_cost: Optional[float] = None
    co2: Optional[float] = None
    nh3: Optional[float] = None
    so2: Optional[float] = None
    nox: Optional[float] = None
    pm2_5: Optional[float] = None
    pm5: Optional[float] = None
    pm10: Optional[float] = None
    nmvoc: Optional[float] = None
    op1: Optional[float] = None
    op2: Optional[float] = None
    op3: Optional[float] = None
    op4: Optional[float] = None
    op5: Optional[float] = None
    cost_generation: Optional[ThermalCostGeneration] = None
    efficiency: Optional[float] = None
    variable_o_m_cost: Optional[float] = None


def check_min_version(data: Any, field: str, version: StudyVersion) -> None:
    if getattr(data, field) is not None:
        raise ValueError(f"Field {field} is not supported in version {version}")


# TODO SL: we could centralize fields definitions so that min version and default values are defined in one place


# TODO SL: we could defined and use a protocol here, for better type checking
#          But adds some boiler plate again
def validate_against_version(
    version: StudyVersion,
    cluster_data: ThermalCluster | ThermalClusterCreation | ThermalClusterFileData | ThermalClusterUpdate,
) -> None:
    if version < STUDY_VERSION_8_6:
        for field in ["nh3", "so2", "nox", "pm2_5", "pm5", "pm10", "nmvoc", "op1", "op2", "op3", "op4", "op5"]:
            check_min_version(cluster_data, field, version)

    if version < STUDY_VERSION_8_7:
        for field in ["cost_generation", "efficiency", "variable_o_m_cost"]:
            check_min_version(cluster_data, field, version)


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
    Creates a thermal cluster from the creation request.
    """
    cluster = ThermalCluster.model_validate(cluster_data.model_dump(exclude_none=True))
    validate_against_version(version, cluster_data)
    initialize_thermal_cluster(cluster, version)
    return cluster


def update_thermal_cluster(cluster: ThermalCluster, data: ThermalClusterUpdate) -> ThermalCluster:
    return cluster.model_copy(update=data.model_dump(exclude_none=True))
