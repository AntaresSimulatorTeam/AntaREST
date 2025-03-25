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
from typing import Any, List

import pytest
from antares.study.version import StudyVersion

from antarest.core.exceptions import InvalidFieldForVersionError
from antarest.study.business.model.thermal_cluster_model import (
    LawOption,
    LocalTSGenerationBehavior,
    ThermalCluster,
    ThermalClusterCreation,
    ThermalClusterGroup,
    ThermalClusterUpdate,
    ThermalCostGeneration,
    create_thermal_cluster,
    update_thermal_cluster,
    validate_thermal_cluster_against_version,
)
from antarest.study.model import STUDY_VERSION_7_2, STUDY_VERSION_8_6, STUDY_VERSION_8_7


def test_thermal_cluster_creation_default_values():
    cluster = create_thermal_cluster(ThermalClusterCreation(name="Cluster @"), version=STUDY_VERSION_7_2)
    assert cluster.model_dump() == {
        "id": "Cluster",
        "name": "Cluster @",
        "unit_count": 1,
        "nominal_capacity": 0.0,
        "enabled": True,
        "group": ThermalClusterGroup.OTHER1,
        "gen_ts": LocalTSGenerationBehavior.USE_GLOBAL,
        "min_stable_power": 0.0,
        "min_up_time": 1,
        "min_down_time": 1,
        "must_run": False,
        "spinning": 0.0,
        "volatility_forced": 0.0,
        "volatility_planned": 0.0,
        "law_forced": LawOption.UNIFORM,
        "law_planned": LawOption.UNIFORM,
        "marginal_cost": 0.0,
        "spread_cost": 0.0,
        "fixed_cost": 0.0,
        "startup_cost": 0.0,
        "market_bid_cost": 0.0,
        "co2": 0,
        "nh3": None,
        "so2": None,
        "nox": None,
        "pm2_5": None,
        "pm5": None,
        "pm10": None,
        "nmvoc": None,
        "op1": None,
        "op2": None,
        "op3": None,
        "op4": None,
        "op5": None,
        "cost_generation": None,
        "efficiency": None,
        "variable_o_m_cost": None,
    }

    cluster = create_thermal_cluster(ThermalClusterCreation(name="Cluster @"), version=STUDY_VERSION_8_6)
    assert cluster.model_dump() == {
        "id": "Cluster",
        "name": "Cluster @",
        "unit_count": 1,
        "nominal_capacity": 0.0,
        "enabled": True,
        "group": ThermalClusterGroup.OTHER1,
        "gen_ts": LocalTSGenerationBehavior.USE_GLOBAL,
        "min_stable_power": 0.0,
        "min_up_time": 1,
        "min_down_time": 1,
        "must_run": False,
        "spinning": 0.0,
        "volatility_forced": 0.0,
        "volatility_planned": 0.0,
        "law_forced": LawOption.UNIFORM,
        "law_planned": LawOption.UNIFORM,
        "marginal_cost": 0.0,
        "spread_cost": 0.0,
        "fixed_cost": 0.0,
        "startup_cost": 0.0,
        "market_bid_cost": 0.0,
        "co2": 0,
        "nh3": 0,
        "so2": 0,
        "nox": 0,
        "pm2_5": 0,
        "pm5": 0,
        "pm10": 0,
        "nmvoc": 0,
        "op1": 0,
        "op2": 0,
        "op3": 0,
        "op4": 0,
        "op5": 0,
        "cost_generation": None,
        "efficiency": None,
        "variable_o_m_cost": None,
    }

    cluster = create_thermal_cluster(ThermalClusterCreation(name="Cluster @"), version=STUDY_VERSION_8_7)
    assert cluster.model_dump() == {
        "id": "Cluster",
        "name": "Cluster @",
        "unit_count": 1,
        "nominal_capacity": 0.0,
        "enabled": True,
        "group": ThermalClusterGroup.OTHER1,
        "gen_ts": LocalTSGenerationBehavior.USE_GLOBAL,
        "min_stable_power": 0.0,
        "min_up_time": 1,
        "min_down_time": 1,
        "must_run": False,
        "spinning": 0.0,
        "volatility_forced": 0.0,
        "volatility_planned": 0.0,
        "law_forced": LawOption.UNIFORM,
        "law_planned": LawOption.UNIFORM,
        "marginal_cost": 0.0,
        "spread_cost": 0.0,
        "fixed_cost": 0.0,
        "startup_cost": 0.0,
        "market_bid_cost": 0.0,
        "co2": 0,
        "nh3": 0,
        "so2": 0,
        "nox": 0,
        "pm2_5": 0,
        "pm5": 0,
        "pm10": 0,
        "nmvoc": 0,
        "op1": 0,
        "op2": 0,
        "op3": 0,
        "op4": 0,
        "op5": 0,
        "cost_generation": ThermalCostGeneration.SET_MANUALLY,
        "efficiency": 100,
        "variable_o_m_cost": 0,
    }


@pytest.mark.parametrize(
    "versions, fields",
    [
        ([STUDY_VERSION_7_2], {"nh3": 0}),
        ([STUDY_VERSION_7_2], {"so2": 0}),
        ([STUDY_VERSION_7_2], {"nox": 0}),
        ([STUDY_VERSION_7_2], {"pm2_5": 0}),
        ([STUDY_VERSION_7_2], {"pm5": 0}),
        ([STUDY_VERSION_7_2], {"pm10": 0}),
        ([STUDY_VERSION_7_2], {"nmvoc": 0}),
        ([STUDY_VERSION_7_2], {"op1": 0}),
        ([STUDY_VERSION_7_2], {"op2": 0}),
        ([STUDY_VERSION_7_2], {"op3": 0}),
        ([STUDY_VERSION_7_2], {"op4": 0}),
        ([STUDY_VERSION_7_2], {"op5": 0}),
        ([STUDY_VERSION_7_2, STUDY_VERSION_8_6], {"cost_generation": ThermalCostGeneration.USE_COST_TIME_SERIES}),
        ([STUDY_VERSION_7_2, STUDY_VERSION_8_6], {"efficiency": 50}),
        ([STUDY_VERSION_7_2, STUDY_VERSION_8_6], {"variable_o_m_cost": 10}),
    ],
)
def test_thermal_cluster_creation_invalid_fields(versions: List[StudyVersion], fields: dict[str, Any]):
    for version in versions:
        with pytest.raises(InvalidFieldForVersionError, match="is not a valid field for study version"):
            create_thermal_cluster(ThermalClusterCreation(name="Cluster @", **fields), version=version)


def test_thermal_cluster_creation_all_values():
    cluster = create_thermal_cluster(
        ThermalClusterCreation(
            name="Cluster @",
            unit_count=100,
            nominal_capacity=1000.0,
            enabled=False,
            group=ThermalClusterGroup.GAS,
            gen_ts=LocalTSGenerationBehavior.USE_GLOBAL,
            min_stable_power=10,
            marginal_cost=30,
            market_bid_cost=40,
            must_run=True,
            spinning=3,
            volatility_forced=5.0,
            volatility_planned=7.0,
            law_forced=LawOption.GEOMETRIC,
            law_planned=LawOption.UNIFORM,
            spread_cost=1,
            fixed_cost=2,
            startup_cost=3,
            min_up_time=4,
            min_down_time=5,
            co2=1,
            nh3=2,
            so2=3,
            nox=4,
            pm2_5=5,
            pm5=6,
            pm10=7,
            nmvoc=8,
            op1=9,
            op2=10,
            op3=11,
            op4=12,
            op5=13,
            cost_generation=ThermalCostGeneration.USE_COST_TIME_SERIES,
            efficiency=10,
            variable_o_m_cost=15,
        ),
        STUDY_VERSION_8_7,
    )

    assert cluster == ThermalCluster(
        id="Cluster",
        name="Cluster @",
        unit_count=100,
        nominal_capacity=1000.0,
        enabled=False,
        group=ThermalClusterGroup.GAS,
        gen_ts=LocalTSGenerationBehavior.USE_GLOBAL,
        min_stable_power=10,
        marginal_cost=30,
        market_bid_cost=40,
        must_run=True,
        spinning=3,
        volatility_forced=5.0,
        volatility_planned=7.0,
        law_forced=LawOption.GEOMETRIC,
        law_planned=LawOption.UNIFORM,
        spread_cost=1,
        fixed_cost=2,
        startup_cost=3,
        min_up_time=4,
        min_down_time=5,
        co2=1,
        nh3=2,
        so2=3,
        nox=4,
        pm2_5=5,
        pm5=6,
        pm10=7,
        nmvoc=8,
        op1=9,
        op2=10,
        op3=11,
        op4=12,
        op5=13,
        cost_generation=ThermalCostGeneration.USE_COST_TIME_SERIES,
        efficiency=10,
        variable_o_m_cost=15,
    )


@pytest.mark.parametrize(
    "invalid_versions,valid_versions,fields",
    [
        ([STUDY_VERSION_7_2], [STUDY_VERSION_8_6, STUDY_VERSION_8_7], {"nh3": 0}),
        ([STUDY_VERSION_7_2], [STUDY_VERSION_8_6, STUDY_VERSION_8_7], {"so2": 0}),
        ([STUDY_VERSION_7_2], [STUDY_VERSION_8_6, STUDY_VERSION_8_7], {"nox": 0}),
        ([STUDY_VERSION_7_2], [STUDY_VERSION_8_6, STUDY_VERSION_8_7], {"pm2_5": 0}),
        ([STUDY_VERSION_7_2], [STUDY_VERSION_8_6, STUDY_VERSION_8_7], {"pm5": 0}),
        ([STUDY_VERSION_7_2], [STUDY_VERSION_8_6, STUDY_VERSION_8_7], {"pm10": 0}),
        ([STUDY_VERSION_7_2], [STUDY_VERSION_8_6, STUDY_VERSION_8_7], {"nmvoc": 0}),
        ([STUDY_VERSION_7_2], [STUDY_VERSION_8_6, STUDY_VERSION_8_7], {"op1": 0}),
        ([STUDY_VERSION_7_2], [STUDY_VERSION_8_6, STUDY_VERSION_8_7], {"op2": 0}),
        ([STUDY_VERSION_7_2], [STUDY_VERSION_8_6, STUDY_VERSION_8_7], {"op3": 0}),
        ([STUDY_VERSION_7_2], [STUDY_VERSION_8_6, STUDY_VERSION_8_7], {"op4": 0}),
        ([STUDY_VERSION_7_2], [STUDY_VERSION_8_6, STUDY_VERSION_8_7], {"op5": 0}),
        (
            [STUDY_VERSION_7_2, STUDY_VERSION_8_6],
            [STUDY_VERSION_8_7],
            {"cost_generation": ThermalCostGeneration.USE_COST_TIME_SERIES},
        ),
        ([STUDY_VERSION_7_2, STUDY_VERSION_8_6], [STUDY_VERSION_8_7], {"efficiency": 50}),
        ([STUDY_VERSION_7_2, STUDY_VERSION_8_6], [STUDY_VERSION_8_7], {"variable_o_m_cost": 10}),
    ],
)
def test_thermal_cluster_version_validation(
    invalid_versions: List[StudyVersion], valid_versions: List[StudyVersion], fields: dict[str, Any]
):
    """
    Check that the presence of the fields raise an error for "invalid_versions", but not for "valid_versions"
    """
    cluster = ThermalCluster(name="my cluster", unit_count=100, nominal_capacity=1000.0, enabled=True, **fields)
    for version in invalid_versions:
        with pytest.raises(InvalidFieldForVersionError, match="is not a valid field for study version"):
            validate_thermal_cluster_against_version(version, cluster)
    for version in valid_versions:
        validate_thermal_cluster_against_version(version, cluster)


def test_thermal_cluster_update():
    cluster = create_thermal_cluster(
        ThermalClusterCreation(
            name="Cluster @",
            unit_count=100,
            nominal_capacity=1000.0,
            enabled=False,
            group=ThermalClusterGroup.GAS,
            gen_ts=LocalTSGenerationBehavior.USE_GLOBAL,
            min_stable_power=10,
            marginal_cost=30,
            market_bid_cost=40,
            must_run=True,
            spinning=3,
            volatility_forced=5.0,
            volatility_planned=7.0,
            law_forced=LawOption.GEOMETRIC,
            law_planned=LawOption.UNIFORM,
            spread_cost=1,
            fixed_cost=2,
            startup_cost=3,
            min_up_time=4,
            min_down_time=5,
            co2=1,
            nh3=2,
            so2=3,
            nox=4,
            pm2_5=5,
            pm5=6,
            pm10=7,
            nmvoc=8,
            op1=9,
            op2=10,
            op3=11,
            op4=12,
            op5=13,
            cost_generation=ThermalCostGeneration.USE_COST_TIME_SERIES,
            efficiency=10,
            variable_o_m_cost=15,
        ),
        STUDY_VERSION_8_7,
    )

    update = ThermalClusterUpdate(
        unit_count=50,
        nominal_capacity=500.0,
        op1=18,
        op2=24,
    )

    updated_cluster = update_thermal_cluster(cluster, update)
    assert updated_cluster == ThermalCluster(
        id="Cluster",
        name="Cluster @",
        unit_count=50,
        nominal_capacity=500.0,
        enabled=False,
        group=ThermalClusterGroup.GAS,
        gen_ts=LocalTSGenerationBehavior.USE_GLOBAL,
        min_stable_power=10,
        marginal_cost=30,
        market_bid_cost=40,
        must_run=True,
        spinning=3,
        volatility_forced=5.0,
        volatility_planned=7.0,
        law_forced=LawOption.GEOMETRIC,
        law_planned=LawOption.UNIFORM,
        spread_cost=1,
        fixed_cost=2,
        startup_cost=3,
        min_up_time=4,
        min_down_time=5,
        co2=1,
        nh3=2,
        so2=3,
        nox=4,
        pm2_5=5,
        pm5=6,
        pm10=7,
        nmvoc=8,
        op1=18,
        op2=24,
        op3=11,
        op4=12,
        op5=13,
        cost_generation=ThermalCostGeneration.USE_COST_TIME_SERIES,
        efficiency=10,
        variable_o_m_cost=15,
    )
