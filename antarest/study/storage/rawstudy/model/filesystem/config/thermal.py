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
from antarest.study.business.model.thermal_model import (
    LawOption,
    LocalTSGenerationBehavior,
    ThermalCluster,
    ThermalClusterGroup,
    ThermalCostGeneration,
    initialize_thermal_cluster,
    validate_thermal_cluster_against_version,
)


class ThermalClusterFileData(AntaresBaseModel):
    """
    Thermal cluster data parsed from INI file.
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

    def to_model(self) -> ThermalCluster:
        return ThermalCluster.model_validate(self.model_dump())

    @classmethod
    def from_model(cls, study_version: StudyVersion, cluster: ThermalCluster) -> "ThermalClusterFileData":
        return cls.model_validate(cluster.model_dump(exclude={"id"}))


def parse_thermal_cluster(study_version: StudyVersion, data: Any) -> ThermalCluster:
    cluster = ThermalClusterFileData.model_validate(data).to_model()
    validate_thermal_cluster_against_version(study_version, cluster)
    initialize_thermal_cluster(cluster, study_version)
    return cluster


def serialize_thermal_cluster(study_version: StudyVersion, cluster: ThermalCluster) -> dict[str, Any]:
    return ThermalClusterFileData.from_model(study_version, cluster).model_dump(by_alias=True, exclude_none=True)
