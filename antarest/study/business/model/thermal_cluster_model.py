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
"""
Defines business models for thermal clusters and corresponding operations (creation, update).

Design notes:
the 3 models defined here share a lot of attributes: that duplication is made on purpose.
The 3 classes model different things or operations, and have actually discrepancies in particular in
the optionality of their attributes.
Also, they should not be used interchangeably in functionalities, which rules out inheritance between them.

However, some functions may accept any of those 3 models, like for example the validation
against a study version.
For that purpose, it's important to keep consistency between the naming of the attributes.

The default values of the business model are carried by the main `ThermalCluster` model,
not the creation model, which will rely on the former one. This makes it possible to rely
on those default values in other parts of the code: parsers, tests ...

"""

from typing import Annotated, Any, MutableMapping, Optional, TypeAlias, cast

from antares.study.version import StudyVersion
from pydantic import ConfigDict, Field, field_validator, model_validator
from pydantic.alias_generators import to_camel
from typing_extensions import override

from antarest.core.exceptions import InvalidFieldForVersionError
from antarest.core.model import LowerCaseId
from antarest.core.serde import AntaresBaseModel
from antarest.study.business.enum_ignore_case import EnumIgnoreCase
from antarest.study.model import STUDY_VERSION_8_6, STUDY_VERSION_8_7
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.config.validation import ItemName


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


# Validation helpers
UnitCount: TypeAlias = Annotated[int, Field(ge=1)]
NominalCapacity: TypeAlias = Annotated[float, Field(ge=0)]
Spinning: TypeAlias = Annotated[float, Field(ge=0, le=100)]
Emission: TypeAlias = Annotated[float, Field(ge=0)]
Efficiency: TypeAlias = Annotated[float, Field(gt=0, le=100)]
Cost: TypeAlias = Annotated[float, Field(ge=0)]
Volatility: TypeAlias = Annotated[float, Field(ge=0, le=1)]


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
    unit_count: UnitCount = 1
    nominal_capacity: NominalCapacity = 0
    enabled: bool = True
    group: ThermalClusterGroup = ThermalClusterGroup.OTHER1
    gen_ts: LocalTSGenerationBehavior = LocalTSGenerationBehavior.USE_GLOBAL
    min_stable_power: float = 0
    min_up_time: int = 1
    min_down_time: int = 1
    must_run: bool = False
    spinning: Spinning = 0
    volatility_forced: Volatility = 0
    volatility_planned: Volatility = 0
    law_forced: LawOption = LawOption.UNIFORM
    law_planned: LawOption = LawOption.UNIFORM
    marginal_cost: Cost = 0
    spread_cost: Cost = 0
    fixed_cost: Cost = 0
    startup_cost: Cost = 0
    market_bid_cost: Cost = 0
    co2: Emission = 0

    # Added in 8.6
    nh3: Optional[Emission] = None
    so2: Optional[Emission] = None
    nox: Optional[Emission] = None
    pm2_5: Optional[Emission] = None
    pm5: Optional[Emission] = None
    pm10: Optional[Emission] = None
    nmvoc: Optional[Emission] = None
    op1: Optional[Emission] = None
    op2: Optional[Emission] = None
    op3: Optional[Emission] = None
    op4: Optional[Emission] = None
    op5: Optional[Emission] = None

    # Added in 8.7
    cost_generation: Optional[ThermalCostGeneration] = None
    efficiency: Optional[Efficiency] = None
    variable_o_m_cost: Optional[Cost] = None

    @field_validator("min_down_time", "min_up_time", mode="before")
    @classmethod
    def _validate_min_up_and_down_time(cls, v: int) -> int:
        return 1 if v < 1 else 168 if v > 168 else v


class ThermalClusterCreation(AntaresBaseModel):
    """
    Represents a creation request for a thermal cluster.

    Most fields are optional: at creation time, default values of the thermal cluster
    model will be used.
    """

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
    unit_count: Optional[UnitCount] = None
    nominal_capacity: Optional[NominalCapacity] = None
    enabled: Optional[bool] = None
    group: Optional[ThermalClusterGroup] = None
    gen_ts: Optional[LocalTSGenerationBehavior] = None
    min_stable_power: Optional[float] = None
    min_up_time: Optional[int] = None
    min_down_time: Optional[int] = None
    must_run: Optional[bool] = None
    spinning: Optional[Spinning] = None
    volatility_forced: Optional[Volatility] = None
    volatility_planned: Optional[Volatility] = None
    law_forced: Optional[LawOption] = None
    law_planned: Optional[LawOption] = None
    marginal_cost: Optional[Cost] = None
    spread_cost: Optional[Cost] = None
    fixed_cost: Optional[Cost] = None
    startup_cost: Optional[Cost] = None
    market_bid_cost: Optional[Cost] = None
    co2: Optional[Emission] = None
    nh3: Optional[Emission] = None
    so2: Optional[Emission] = None
    nox: Optional[Emission] = None
    pm2_5: Optional[Emission] = None
    pm5: Optional[Emission] = None
    pm10: Optional[Emission] = None
    nmvoc: Optional[Emission] = None
    op1: Optional[Emission] = None
    op2: Optional[Emission] = None
    op3: Optional[Emission] = None
    op4: Optional[Emission] = None
    op5: Optional[Emission] = None
    cost_generation: Optional[ThermalCostGeneration] = None
    efficiency: Optional[Efficiency] = None
    variable_o_m_cost: Optional[Cost] = None

    @field_validator("min_down_time", "min_up_time", mode="before")
    @classmethod
    def _validate_min_up_and_down_time(cls, v: int) -> int:
        return 1 if v < 1 else 168 if v > 168 else v

    @classmethod
    def from_cluster(cls, cluster: ThermalCluster) -> "ThermalClusterCreation":
        """
        Conversion to creation request, can be useful for duplicating clusters.
        """
        return ThermalClusterCreation.model_validate(cluster.model_dump(mode="json", exclude={"id"}, exclude_none=True))


class ThermalClusterUpdate(AntaresBaseModel):
    """
    Represents an update of a thermal cluster.

    Only not-None fields will be used to update the thermal cluster.
    """

    class Config:
        alias_generator = to_camel
        extra = "forbid"
        populate_by_name = True

        @staticmethod
        def json_schema_extra(schema: MutableMapping[str, Any]) -> None:
            schema["example"] = ThermalClusterUpdate(
                group="Gas",
                enabled=False,
                unit_count=100,
                nominal_capacity=1000.0,
                gen_ts="use global",
                co2=7.0,
            ).model_dump(mode="json")

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

    unit_count: Optional[UnitCount] = None
    nominal_capacity: Optional[NominalCapacity] = None
    enabled: Optional[bool] = None
    group: Optional[ThermalClusterGroup] = None
    gen_ts: Optional[LocalTSGenerationBehavior] = None
    min_stable_power: Optional[float] = None
    min_up_time: Optional[int] = None
    min_down_time: Optional[int] = None
    must_run: Optional[bool] = None
    spinning: Optional[Spinning] = None
    volatility_forced: Optional[Volatility] = None
    volatility_planned: Optional[Volatility] = None
    law_forced: Optional[LawOption] = None
    law_planned: Optional[LawOption] = None
    marginal_cost: Optional[Cost] = None
    spread_cost: Optional[Cost] = None
    fixed_cost: Optional[Cost] = None
    startup_cost: Optional[Cost] = None
    market_bid_cost: Optional[Cost] = None
    co2: Optional[Emission] = None
    nh3: Optional[Emission] = None
    so2: Optional[Emission] = None
    nox: Optional[Emission] = None
    pm2_5: Optional[Emission] = None
    pm5: Optional[Emission] = None
    pm10: Optional[Emission] = None
    nmvoc: Optional[Emission] = None
    op1: Optional[Emission] = None
    op2: Optional[Emission] = None
    op3: Optional[Emission] = None
    op4: Optional[Emission] = None
    op5: Optional[Emission] = None
    cost_generation: Optional[ThermalCostGeneration] = None
    efficiency: Optional[Efficiency] = None
    variable_o_m_cost: Optional[Cost] = None

    @field_validator("min_down_time", "min_up_time", mode="before")
    @classmethod
    def _validate_min_up_and_down_time(cls, v: int) -> int:
        return 1 if v < 1 else 168 if v > 168 else v


ThermalClusterUpdates = dict[LowerCaseId, dict[LowerCaseId, ThermalClusterUpdate]]


def _check_min_version(data: Any, field: str, version: StudyVersion) -> None:
    if getattr(data, field) is not None:
        raise InvalidFieldForVersionError(f"Field {field} is not a valid field for study version {version}")


def validate_thermal_cluster_against_version(
    version: StudyVersion,
    cluster_data: ThermalCluster | ThermalClusterCreation | ThermalClusterUpdate,
) -> None:
    """
    Validates input thermal cluster data against the provided study versions

    Will raise an InvalidFieldForVersionError if a field is not valid for the given study version.
    """
    if version < STUDY_VERSION_8_6:
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
