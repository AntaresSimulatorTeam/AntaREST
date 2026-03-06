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

from antarest.core.exceptions import AreaNotFound, RenewableClusterNotFound
from antarest.study.business.model.renewable_cluster_model import (
    RenewableCluster,
    RenewableClusterGroup,
    TimeSeriesInterpretation,
)
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.dao.database.models.renewable import RENEWABLE_CLUSTER_TABLE, RENEWABLE_SERIES_TABLE


def test_save_renewable_creates_cluster(db_dao: DatabaseStudyDao) -> None:
    dao = db_dao
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


def test_save_renewable_overwrites_existing(db_dao: DatabaseStudyDao) -> None:
    dao = db_dao
    dao.save_area("Paris")

    dao.save_renewable("paris", RenewableCluster(id="gas", name="Gas", nominal_capacity=100.0))
    dao.save_renewable("paris", RenewableCluster(id="gas", name="Gas", nominal_capacity=200.0))

    result = dao.get_renewable("paris", "gas")
    assert result.nominal_capacity == 200.0


def test_save_multiple_renewable_clusters(db_dao: DatabaseStudyDao) -> None:
    dao = db_dao
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


def test_get_one_renewable_cluster(db_dao: DatabaseStudyDao) -> None:
    dao = db_dao
    dao.save_area("Paris")
    dao.save_renewable("paris", RenewableCluster(id="battery", name="Battery"))

    cluster = dao.get_renewable("paris", "battery")
    assert cluster.id == "battery"
    assert cluster.name == "Battery"

    with pytest.raises(RenewableClusterNotFound):
        dao.get_renewable("paris", "nonexistent")

    with pytest.raises(AreaNotFound):
        dao.get_renewable("nonexistent", "battery")


def test_get_all_renewables(db_dao: DatabaseStudyDao) -> None:
    dao = db_dao
    dao.save_area("Paris")
    dao.save_area("London")

    dao.save_renewable("paris", RenewableCluster(id="battery", name="Battery"))
    dao.save_renewable("london", RenewableCluster(id="wind", name="Wind"))

    all_renewables = dao.get_all_renewables()
    assert set(all_renewables.keys()) == {"paris", "london"}
    assert set(all_renewables["paris"].keys()) == {"battery"}
    assert set(all_renewables["london"].keys()) == {"wind"}

    with pytest.raises(AreaNotFound):
        dao.get_all_renewables_for_area("nonexistent")


def test_delete_renewable(db_dao: DatabaseStudyDao) -> None:
    dao = db_dao
    dao.save_area("Paris")
    renewable = RenewableCluster(id="battery", name="Battery")
    dao.save_renewable("paris", renewable)

    assert dao.renewable_exists("paris", "battery")

    with pytest.raises(RenewableClusterNotFound):
        dao.delete_renewable("paris", RenewableCluster(id="fake", name="fake"))
    with pytest.raises(AreaNotFound):
        dao.delete_renewable("paris2", renewable)

    dao.delete_renewable("paris", renewable)
    assert not dao.renewable_exists("paris", "battery")

    with pytest.raises(RenewableClusterNotFound):
        dao.get_renewable("paris", "battery")

    with pytest.raises(RenewableClusterNotFound):
        dao.delete_renewable("paris", renewable)


def test_renewable_exists_returns_false_for_unknown_area(db_dao: DatabaseStudyDao) -> None:
    assert not db_dao.renewable_exists("nonexistent", "gas")


def test_renewable_series_lifecycle(db_session: Session, db_dao: DatabaseStudyDao) -> None:
    dao = db_dao
    dao.save_area("Paris")
    renewable = RenewableCluster(id="battery", name="Battery")
    dao.save_renewable("paris", renewable)

    matrix_service = dao._matrix_service
    dataframe = pl.DataFrame(data=[[1, 2.5], [3, 4.7]], orient="row")
    series_id = matrix_service.create(dataframe)

    dao.save_renewable_series("paris", "battery", series_id)
    pl.testing.assert_frame_equal(dao.get_renewable_series("paris", "battery"), dataframe, check_dtypes=False)

    dao.delete_renewable("paris", renewable)

    with db_session:
        assert db_session.execute(select(RENEWABLE_CLUSTER_TABLE)).fetchall() == []
        assert db_session.execute(select(RENEWABLE_SERIES_TABLE)).fetchall() == []


def test_get_renewable_matrix_raises_when_missing(db_dao: DatabaseStudyDao) -> None:
    dao = db_dao
    dao.save_area("Paris")
    dao.save_renewable("paris", RenewableCluster(id="battery", name="Battery"))

    with pytest.raises(RenewableClusterNotFound):
        dao.get_renewable_series("paris", "gas")
    with pytest.raises(AreaNotFound):
        dao.get_renewable_series("nonexistent", "gas")


def test_save_renewable_matrix_raises_when_missing(db_dao: DatabaseStudyDao) -> None:
    dao = db_dao
    dao.save_area("Paris")

    with pytest.raises(RenewableClusterNotFound):
        dao.save_renewable_series("paris", "gas", "missing-matrix-id")
    with pytest.raises(AreaNotFound):
        dao.save_renewable_series("nonexistent", "gas", "missing-matrix-id")


def test_area_with_no_clusters_are_absent_from_clusters_dict(db_dao: DatabaseStudyDao) -> None:
    dao = db_dao
    dao.save_area("germany")
    dao.save_area("italy")

    dao.save_renewable("germany", RenewableCluster(id="battery", name="Battery"))

    clusters = dao.get_all_renewables()

    assert "italy" not in clusters
    assert "germany" in clusters
    assert "battery" in clusters["germany"]
