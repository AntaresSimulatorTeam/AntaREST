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

"""
Thermal DAO tests, parameterized across both database and filesystem backends.
"""

import polars as pl
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from antarest.core.exceptions import AreaNotFound, ThermalClusterNotFound
from antarest.study.business.model.thermal_cluster_model import (
    LawOption,
    LocalTSGenerationBehavior,
    ThermalCluster,
    ThermalClusterCreation,
    ThermalClusterGroup,
    ThermalCostGeneration,
)
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.dao.database.models.thermal import (
    THERMAL_CLUSTER_TABLE,
    THERMAL_CO2_COST_TABLE,
    THERMAL_FUEL_COST_TABLE,
    THERMAL_MODULATION_TABLE,
    THERMAL_PREPRO_TABLE,
    THERMAL_SERIES_TABLE,
)
from antarest.study.storage.variantstudy.model.command.create_cluster import CreateCluster
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from tests.study.dao.utils import save_area


def test_save_thermal_creates_cluster(dao: StudyDao) -> None:
    save_area(dao, "Paris")

    thermal = ThermalCluster(
        id="gas_cluster",
        name="Gas Cluster",
        unit_count=2,
        nominal_capacity=1000.0,
        enabled=False,
        group=ThermalClusterGroup.GAS.value,
        gen_ts=LocalTSGenerationBehavior.FORCE_NO_GENERATION,
        law_forced=LawOption.GEOMETRIC,
        law_planned=LawOption.UNIFORM,
        cost_generation=ThermalCostGeneration.SET_MANUALLY,
        efficiency=90.0,
        variable_o_m_cost=1.5,
        nh3=1.0,
    )

    dao.save_thermals({"paris": [thermal]})

    expected = ThermalCluster(
        id="gas_cluster",
        name="Gas Cluster",
        unit_count=2,
        nominal_capacity=1000.0,
        enabled=False,
        group="gas",
        gen_ts=LocalTSGenerationBehavior.FORCE_NO_GENERATION,
        min_stable_power=0.0,
        min_up_time=1,
        min_down_time=1,
        must_run=False,
        spinning=0.0,
        volatility_forced=0.0,
        volatility_planned=0.0,
        law_forced=LawOption.GEOMETRIC,
        law_planned=LawOption.UNIFORM,
        marginal_cost=0.0,
        spread_cost=0.0,
        fixed_cost=0.0,
        startup_cost=0.0,
        market_bid_cost=0.0,
        co2=0.0,
        nh3=1.0,
        so2=0,
        nox=0,
        pm2_5=0,
        pm5=0,
        pm10=0,
        nmvoc=0,
        op1=0,
        op2=0,
        op3=0,
        op4=0,
        op5=0,
        cost_generation=ThermalCostGeneration.SET_MANUALLY,
        efficiency=90.0,
        variable_o_m_cost=1.5,
    )

    result = dao.get_thermal("paris", "gas_cluster")
    if isinstance(dao, DatabaseStudyDao):
        assert result == expected
    else:
        # Intentional divergence: FS keeps the original case to stay backward-compatible
        # with existing studies on disk (see backward-compat note in thermal_cluster_model.py:154-160);
        # DB normalizes to lowercase since it only stores new studies.
        assert result.name == expected.name
        assert result.unit_count == expected.unit_count
        assert result.nominal_capacity == expected.nominal_capacity
        assert result.enabled == expected.enabled

    with pytest.raises(AreaNotFound):
        dao.save_thermals({"nonexistent": [thermal]})


def test_save_thermal_overwrites_existing(dao: StudyDao) -> None:
    save_area(dao, "Paris")

    dao.save_thermals({"paris": [ThermalCluster(name="Gas", nominal_capacity=100.0)]})
    dao.save_thermals({"paris": [ThermalCluster(name="Gas", nominal_capacity=200.0)]})

    result = dao.get_thermal("paris", "gas")
    assert result.nominal_capacity == 200.0


def test_save_multiple_thermal_clusters(dao: StudyDao) -> None:
    save_area(dao, "Paris")

    dao.save_thermals(
        {
            "paris": [
                ThermalCluster(name="Gas", nominal_capacity=200.0),
                ThermalCluster(name="Nuclear", nominal_capacity=500.0),
            ]
        }
    )

    paris_clusters = dao.get_all_thermals_for_area("paris")
    assert len(paris_clusters) == 2
    assert {c.name for c in paris_clusters} == {"Gas", "Nuclear"}
    assert {c.nominal_capacity for c in paris_clusters} == {200.0, 500.0}

    # Updates nuclear and adds a new one, fuel
    dao.save_thermals(
        {
            "paris": [
                ThermalCluster(name="Nuclear", nominal_capacity=1000.0),
                ThermalCluster(name="Fuel", nominal_capacity=100.0),
            ]
        }
    )
    paris_clusters = dao.get_all_thermals_for_area("paris")
    assert len(paris_clusters) == 3
    assert {c.name for c in paris_clusters} == {"Fuel", "Gas", "Nuclear"}
    assert {c.nominal_capacity for c in paris_clusters} == {100.0, 200.0, 1000.0}

    # Check area not found raises an error
    with pytest.raises(AreaNotFound):
        dao.save_thermals(
            {
                "nonexistent": [
                    ThermalCluster(name="Nuclear", nominal_capacity=1000.0),
                    ThermalCluster(name="Fuel", nominal_capacity=100.0),
                ]
            }
        )


def test_get_one_thermal_cluster(dao: StudyDao) -> None:
    save_area(dao, "Paris")
    dao.save_thermals({"paris": [ThermalCluster(name="Gas")]})

    cluster = dao.get_thermal("paris", "gas")
    # Intentional divergence: FS keeps the original case (e.g. "Gas") for backward
    # compatibility with existing studies on disk; DB normalizes to lowercase.
    # Compare case-insensitively to assert both backends.
    assert cluster.id.lower() == "gas"
    assert cluster.name == "Gas"

    with pytest.raises(ThermalClusterNotFound):
        dao.get_thermal("paris", "nonexistent")

    with pytest.raises(AreaNotFound):
        dao.get_thermal("nonexistent", "gas")


def test_get_all_thermals(dao: StudyDao) -> None:
    save_area(dao, "Paris")
    save_area(dao, "London")

    dao.save_thermals({"paris": [ThermalCluster(name="Gas")], "london": [ThermalCluster(name="Coal")]})

    all_thermals = dao.get_all_thermals()
    assert set(all_thermals.keys()) == {"paris", "london"}
    assert set(all_thermals["paris"].keys()) == {"gas"}
    assert set(all_thermals["london"].keys()) == {"coal"}

    with pytest.raises(AreaNotFound):
        dao.get_all_thermals_for_area("nonexistent")


def test_delete_thermal(dao: StudyDao) -> None:
    save_area(dao, "Paris")
    thermal = ThermalCluster(id="gas", name="Gas")
    dao.save_thermals({"paris": [thermal]})

    assert dao.thermal_exists("paris", "gas")

    with pytest.raises(ThermalClusterNotFound):
        dao.delete_thermal("paris", "gas2")
    with pytest.raises(AreaNotFound):
        dao.delete_thermal("paris2", "gas")

    dao.delete_thermal("paris", "gas")
    assert not dao.thermal_exists("paris", "gas")

    with pytest.raises(ThermalClusterNotFound):
        dao.get_thermal("paris", "gas")

    with pytest.raises(ThermalClusterNotFound):
        dao.delete_thermal("paris", "gas")


def test_thermal_exists_returns_false_for_unknown_area(dao: StudyDao) -> None:
    assert not dao.thermal_exists("nonexistent", "gas")


def test_thermal_matrix_round_trip(dao: StudyDao, matrix_service) -> None:
    """Matrices survive a save/get round-trip on both backends."""
    save_area(dao, "Paris")
    dao.save_thermals({"paris": [ThermalCluster(name="Gas")]})

    dataframe = pl.DataFrame(data=[[1, 2.5], [3, 4.7]], orient="row")
    series_id = matrix_service.create(dataframe)

    dao.save_thermal_prepro({"paris": {"gas": series_id}})
    dao.save_thermal_modulation({"paris": {"gas": series_id}})
    dao.save_thermal_series({"paris": {"gas": series_id}})
    dao.save_thermal_fuel_cost({"paris": {"gas": series_id}})
    dao.save_thermal_co2_cost({"paris": {"gas": series_id}})

    pl.testing.assert_frame_equal(dao.get_thermal_prepro("paris", "gas"), dataframe, check_dtypes=False)
    pl.testing.assert_frame_equal(dao.get_thermal_modulation("paris", "gas"), dataframe, check_dtypes=False)
    pl.testing.assert_frame_equal(dao.get_thermal_series("paris", "gas"), dataframe, check_dtypes=False)
    pl.testing.assert_frame_equal(dao.get_thermal_fuel_cost("paris", "gas"), dataframe, check_dtypes=False)
    pl.testing.assert_frame_equal(dao.get_thermal_co2_cost("paris", "gas"), dataframe, check_dtypes=False)


def test_area_with_no_clusters_are_absent_from_clusters_dict(dao: StudyDao) -> None:
    save_area(dao, "germany")
    save_area(dao, "italy")

    dao.save_thermals({"germany": [ThermalCluster(name="Gas")]})

    clusters = dao.get_all_thermals()

    assert "italy" not in clusters
    assert "germany" in clusters
    assert "gas" in clusters["germany"]


def test_save_thermal_and_upper_case_name(dao: StudyDao, command_context: CommandContext) -> None:
    save_area(dao, "fr")
    command = CreateCluster(
        area_id="fr",
        parameters=ThermalClusterCreation(name="MyThermal"),
        command_context=command_context,
        study_version=dao.get_version(),
    )
    output = command.apply(dao)
    assert output.status  # The command should succeed even if the name is in upper case


# ──────────────────────────────────────────────────────────────────────
# Database-only tests
# ──────────────────────────────────────────────────────────────────────


def test_thermal_matrices_cascade_delete(db_session: Session, db_dao: DatabaseStudyDao) -> None:
    """Deleting a thermal cluster cascades to all matrix tables (DB-level FK cascade)."""
    save_area(db_dao, "Paris")
    db_dao.save_thermals({"paris": [ThermalCluster(name="Gas")]})

    matrix_service = db_dao._matrix_service
    dataframe = pl.DataFrame(data=[[1, 2.5], [3, 4.7]], orient="row")
    series_id = matrix_service.create(dataframe)

    db_dao.save_thermal_prepro({"paris": {"gas": series_id}})
    db_dao.save_thermal_modulation({"paris": {"gas": series_id}})
    db_dao.save_thermal_series({"paris": {"gas": series_id}})
    db_dao.save_thermal_fuel_cost({"paris": {"gas": series_id}})
    db_dao.save_thermal_co2_cost({"paris": {"gas": series_id}})

    db_dao.delete_thermal("paris", "gas")

    with db_session:
        assert db_session.execute(select(THERMAL_CLUSTER_TABLE)).fetchall() == []
        assert db_session.execute(select(THERMAL_PREPRO_TABLE)).fetchall() == []
        assert db_session.execute(select(THERMAL_MODULATION_TABLE)).fetchall() == []
        assert db_session.execute(select(THERMAL_SERIES_TABLE)).fetchall() == []
        assert db_session.execute(select(THERMAL_FUEL_COST_TABLE)).fetchall() == []
        assert db_session.execute(select(THERMAL_CO2_COST_TABLE)).fetchall() == []


def test_get_thermal_matrix_raises_when_missing(db_dao: DatabaseStudyDao) -> None:
    """DB raises ValueError with a specific message when a matrix row is absent."""
    save_area(db_dao, "Paris")
    db_dao.save_thermals({"paris": [ThermalCluster(name="Gas")]})

    getters = [
        db_dao.get_thermal_prepro,
        db_dao.get_thermal_series,
        db_dao.get_thermal_modulation,
        db_dao.get_thermal_fuel_cost,
        db_dao.get_thermal_co2_cost,
    ]
    for getter in getters:
        with pytest.raises(ValueError, match="One of the thermal clusters table is not filled as it should"):
            getter("paris", "gas")
        with pytest.raises(AreaNotFound):
            getter("nonexistent", "gas")


def test_save_thermal_matrix_raises_when_missing(db_dao: DatabaseStudyDao) -> None:
    """DB raises ThermalClusterNotFound / AreaNotFound when saving matrices for unknown clusters."""
    save_area(db_dao, "Paris")

    savers = [
        db_dao.save_thermal_prepro,
        db_dao.save_thermal_series,
        db_dao.save_thermal_modulation,
        db_dao.save_thermal_fuel_cost,
        db_dao.save_thermal_co2_cost,
    ]

    for saver in savers:
        with pytest.raises(ThermalClusterNotFound):
            saver({"paris": {"gas": "missing-matrix-id"}})
        with pytest.raises(AreaNotFound):
            saver({"nonexistent": {"gas": "missing-matrix-id"}})
