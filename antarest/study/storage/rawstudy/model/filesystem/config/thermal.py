# Copyright (c) 2026, RTE (https://www.rte-france.com)
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
from typing import Any

from antares.study.version import StudyVersion
from pydantic import ConfigDict, Field

from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.string import to_kebab_case
from antarest.study.business.model.thermal_cluster_model import (
    LawOption,
    LocalTSGenerationBehavior,
    ThermalCluster,
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
    unit_count: int | None = Field(default=None, alias="unitcount")
    nominal_capacity: float | None = Field(default=None, alias="nominalcapacity")
    enabled: bool | None = None
    group: str | None = None
    gen_ts: LocalTSGenerationBehavior | None = None
    min_stable_power: float | None = None
    min_up_time: int | None = None
    min_down_time: int | None = None
    must_run: bool | None = None
    spinning: float | None = None
    volatility_forced: float | None = Field(default=None, alias="volatility.forced")
    volatility_planned: float | None = Field(default=None, alias="volatility.planned")
    law_forced: LawOption | None = Field(default=None, alias="law.forced")
    law_planned: LawOption | None = Field(default=None, alias="law.planned")
    marginal_cost: float | None = None
    spread_cost: float | None = None
    fixed_cost: float | None = None
    startup_cost: float | None = None
    market_bid_cost: float | None = None
    co2: float | None = None

    # Added in 8.6
    nh3: float | None = None
    so2: float | None = None
    nox: float | None = None
    pm2_5: float | None = Field(default=None, alias="pm2_5")
    pm5: float | None = None
    pm10: float | None = None
    nmvoc: float | None = None
    op1: float | None = None
    op2: float | None = None
    op3: float | None = None
    op4: float | None = None
    op5: float | None = None

    # Added in 8.7
    cost_generation: ThermalCostGeneration | None = Field(default=None, alias="costgeneration")
    efficiency: float | None = None
    variable_o_m_cost: float | None = Field(default=None, alias="variableomcost")

    def to_model(self) -> ThermalCluster:
        return ThermalCluster.model_validate(self.model_dump(exclude_none=True))

    @classmethod
    def from_model(cls, cluster: ThermalCluster) -> "ThermalClusterFileData":
        return cls.model_validate(cluster.model_dump(exclude={"id"}))


def parse_thermal_cluster(study_version: StudyVersion, data: Any) -> ThermalCluster:
    cluster = ThermalClusterFileData.model_validate(data).to_model()
    validate_thermal_cluster_against_version(study_version, cluster)
    initialize_thermal_cluster(cluster, study_version)
    return cluster


def serialize_thermal_cluster(study_version: StudyVersion, cluster: ThermalCluster) -> dict[str, Any]:
    validate_thermal_cluster_against_version(study_version, cluster)
    return ThermalClusterFileData.from_model(cluster).model_dump(mode="json", by_alias=True, exclude_none=True)
