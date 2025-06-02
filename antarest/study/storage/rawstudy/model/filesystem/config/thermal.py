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
from antarest.study.business.model.thermal_cluster_model import (
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
    unit_count: Optional[int] = Field(default=None, alias="unitcount")
    nominal_capacity: Optional[float] = Field(default=None, alias="nominalcapacity")
    enabled: Optional[bool] = None
    group: Optional[ThermalClusterGroup] = None
    gen_ts: Optional[LocalTSGenerationBehavior] = None
    min_stable_power: Optional[float] = None
    min_up_time: Optional[int] = None
    min_down_time: Optional[int] = None
    must_run: Optional[bool] = None
    spinning: Optional[float] = None
    volatility_forced: Optional[float] = Field(default=None, alias="volatility.forced")
    volatility_planned: Optional[float] = Field(default=None, alias="volatility.planned")
    law_forced: Optional[LawOption] = Field(default=None, alias="law.forced")
    law_planned: Optional[LawOption] = Field(default=None, alias="law.planned")
    marginal_cost: Optional[float] = None
    spread_cost: Optional[float] = None
    fixed_cost: Optional[float] = None
    startup_cost: Optional[float] = None
    market_bid_cost: Optional[float] = None
    co2: Optional[float] = None

    # Added in 8.6
    nh3: Optional[float] = None
    so2: Optional[float] = None
    nox: Optional[float] = None
    pm2_5: Optional[float] = Field(default=None, alias="pm2_5")
    pm5: Optional[float] = None
    pm10: Optional[float] = None
    nmvoc: Optional[float] = None
    op1: Optional[float] = None
    op2: Optional[float] = None
    op3: Optional[float] = None
    op4: Optional[float] = None
    op5: Optional[float] = None

    # Added in 8.7
    cost_generation: Optional[ThermalCostGeneration] = Field(default=None, alias="costgeneration")
    efficiency: Optional[float] = None
    variable_o_m_cost: Optional[float] = Field(default=None, alias="variableomcost")

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
