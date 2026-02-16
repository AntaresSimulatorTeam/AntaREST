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
Unit tests for DatabaseRenewableDao.
"""

import polars as pl
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from antarest.core.exceptions import AreaNotFound, RenewableClusterNotFound, ThermalClusterNotFound
from antarest.study.business.model.renewable_cluster_model import (
    RenewableCluster,
    RenewableClusterGroup,
    TimeSeriesInterpretation,
)
from antarest.study.business.model.thermal_cluster_model import (
    ThermalCluster,
)
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.dao.database.models.thermal import (
    THERMAL_CLUSTER_TABLE,
    THERMAL_CO2_COST_TABLE,
    THERMAL_FUEL_COST_TABLE,
    THERMAL_MODULATION_TABLE,
    THERMAL_PREPRO_TABLE,
    THERMAL_SERIES_TABLE,
)


def test_save_renewable_creates_cluster(dao: DatabaseStudyDao) -> None:
    dao.save_area("Paris")

    renewable = RenewableCluster(
        id="battery",
        name="Battery",
        unit_count=2,
        nominal_capacity=1000.0,
        enabled=False,
        group=RenewableClusterGroup.THERMAL_SOLAR.value,
        ts_interpretation=TimeSeriesInterpretation.PRODUCTION_FACTOR,
    )

    dao.save_renewable("paris", renewable)

    result = dao.get_renewable("paris", "battery")
    assert result == renewable

    with pytest.raises(AreaNotFound):
        dao.save_renewable("nonexistent", renewable)


def test_save_renewable_overwrites_existing(dao: DatabaseStudyDao) -> None:
    dao.save_area("Paris")

    dao.save_renewable("paris", RenewableCluster(id="gas", name="Gas", nominal_capacity=100.0))
    dao.save_renewable("paris", RenewableCluster(id="gas", name="Gas", nominal_capacity=200.0))

    result = dao.get_renewable("paris", "gas")
    assert result.nominal_capacity == 200.0


def test_save_multiple_renewable_clusters(dao: DatabaseStudyDao) -> None:
    dao.save_area("Paris")

    dao.save_renewables(
        "paris",
        [
            RenewableCluster(id="battery", name="Battery", nominal_capacity=200.0),
            RenewableCluster(id="solar panels", name="Solar PaNELS", nominal_capacity=500.0),
        ],
    )

    paris_clusters = dao.get_all_renewables_for_area("paris")
    assert len(paris_clusters) == 2
    assert [c.name for c in paris_clusters] == ["Battery", "Solar PaNELS"]
    assert [c.nominal_capacity for c in paris_clusters] == [200.0, 500.0]

    # Updates nuclear and adds a new one, fuel
    dao.save_renewables(
        "paris",
        [
            RenewableCluster(id="battery", name="Battery", nominal_capacity=1000.0),
            RenewableCluster(id="wind offshore", name="Wind", nominal_capacity=100.0),
        ],
    )
    paris_clusters = dao.get_all_renewables_for_area("paris")
    assert len(paris_clusters) == 3
    assert [c.name for c in paris_clusters] == ["Battery", "Solar PaNELS", "Wind"]
    assert [c.nominal_capacity for c in paris_clusters] == [1000.0, 500.0, 100.0]

    # Check are not found raises an error
    with pytest.raises(AreaNotFound):
        dao.save_renewables(
            "nonexistent",
            [
                RenewableCluster(id="nuclear", name="Nuclear", nominal_capacity=1000.0),
                RenewableCluster(id="fuel", name="Fuel", nominal_capacity=100.0),
            ],
        )


def test_get_one_renewable_cluster(dao: DatabaseStudyDao) -> None:
    dao.save_area("Paris")
    dao.save_renewable("paris", RenewableCluster(id="battery", name="Battery"))

    cluster = dao.get_renewable("paris", "battery")
    assert cluster.id == "battery"
    assert cluster.name == "Battery"

    with pytest.raises(RenewableClusterNotFound):
        dao.get_renewable("paris", "nonexistent")

    with pytest.raises(AreaNotFound):
        dao.get_renewable("nonexistent", "battery")


def test_get_all_thermals(dao: DatabaseStudyDao) -> None:
    dao.save_area("Paris")
    dao.save_area("London")

    dao.save_thermal("paris", ThermalCluster(id="gas", name="Gas"))
    dao.save_thermal("london", ThermalCluster(id="coal", name="Coal"))

    all_thermals = dao.get_all_thermals()
    assert set(all_thermals.keys()) == {"paris", "london"}
    assert set(all_thermals["paris"].keys()) == {"gas"}
    assert set(all_thermals["london"].keys()) == {"coal"}

    with pytest.raises(AreaNotFound):
        dao.get_all_thermals_for_area("nonexistent")


def test_delete_thermal(dao: DatabaseStudyDao) -> None:
    dao.save_area("Paris")
    thermal = ThermalCluster(id="gas", name="Gas")
    dao.save_thermal("paris", thermal)

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


def test_thermal_exists_returns_false_for_unknown_area(dao: DatabaseStudyDao) -> None:
    assert not dao.thermal_exists("nonexistent", "gas")


def test_thermal_matrices_lifecycle(db_session: Session, dao: DatabaseStudyDao) -> None:
    dao.save_area("Paris")
    dao.save_thermal("paris", ThermalCluster(id="gas", name="Gas"))

    matrix_service = dao._matrix_service
    dataframe = pl.DataFrame(data=[[1, 2.5], [3, 4.7]], orient="row")
    series_id = matrix_service.create(dataframe)

    dao.save_thermal_prepro("paris", "gas", series_id)
    dao.save_thermal_modulation("paris", "gas", series_id)
    dao.save_thermal_series("paris", "gas", series_id)
    dao.save_thermal_fuel_cost("paris", "gas", series_id)
    dao.save_thermal_co2_cost("paris", "gas", series_id)

    pl.testing.assert_frame_equal(dao.get_thermal_prepro("paris", "gas"), dataframe, check_dtypes=False)
    pl.testing.assert_frame_equal(dao.get_thermal_modulation("paris", "gas"), dataframe, check_dtypes=False)
    pl.testing.assert_frame_equal(dao.get_thermal_series("paris", "gas"), dataframe, check_dtypes=False)
    pl.testing.assert_frame_equal(dao.get_thermal_fuel_cost("paris", "gas"), dataframe, check_dtypes=False)
    pl.testing.assert_frame_equal(dao.get_thermal_co2_cost("paris", "gas"), dataframe, check_dtypes=False)

    dao.delete_thermal("paris", "gas")

    with db_session:
        assert db_session.execute(select(THERMAL_CLUSTER_TABLE)).fetchall() == []
        assert db_session.execute(select(THERMAL_PREPRO_TABLE)).fetchall() == []
        assert db_session.execute(select(THERMAL_MODULATION_TABLE)).fetchall() == []
        assert db_session.execute(select(THERMAL_SERIES_TABLE)).fetchall() == []
        assert db_session.execute(select(THERMAL_FUEL_COST_TABLE)).fetchall() == []
        assert db_session.execute(select(THERMAL_CO2_COST_TABLE)).fetchall() == []


def test_get_thermal_matrix_raises_when_missing(dao: DatabaseStudyDao) -> None:
    dao.save_area("Paris")
    dao.save_thermal("paris", ThermalCluster(id="gas", name="Gas"))

    getters = [
        dao.get_thermal_prepro,
        dao.get_thermal_series,
        dao.get_thermal_modulation,
        dao.get_thermal_fuel_cost,
        dao.get_thermal_co2_cost,
    ]
    for getter in getters:
        with pytest.raises(ThermalClusterNotFound):
            getter("paris", "gas")
        with pytest.raises(AreaNotFound):
            getter("nonexistent", "gas")


def test_save_thermal_matrix_raises_when_missing(dao: DatabaseStudyDao) -> None:
    dao.save_area("Paris")

    savers = [
        dao.save_thermal_prepro,
        dao.save_thermal_series,
        dao.save_thermal_modulation,
        dao.save_thermal_fuel_cost,
        dao.save_thermal_co2_cost,
    ]

    for saver in savers:
        with pytest.raises(ThermalClusterNotFound):
            saver("paris", "gas", "missing-matrix-id")
        with pytest.raises(AreaNotFound):
            saver("nonexistent", "gas", "missing-matrix-id")


def test_area_with_no_clusters_are_absent_from_clusters_dict(dao: DatabaseStudyDao) -> None:
    dao.save_area("germany")
    dao.save_area("italy")

    dao.save_thermal("germany", ThermalCluster(id="gas", name="Gas"))

    clusters = dao.get_all_thermals()

    assert "italy" not in clusters
    assert "germany" in clusters
    assert "gas" in clusters["germany"]
