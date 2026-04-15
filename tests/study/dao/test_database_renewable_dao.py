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
Unit tests for RenewableDao — run on both database and filesystem backends.
"""

import polars as pl
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from antarest.core.exceptions import AreaNotFound, RenewableClusterNotFound
from antarest.study.business.model.renewable_cluster_model import (
    RenewableCluster,
    RenewableClusterCreation,
    RenewableClusterGroup,
    TimeSeriesInterpretation,
)
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.dao.database.models.renewable import RENEWABLE_CLUSTER_TABLE, RENEWABLE_SERIES_TABLE
from antarest.study.storage.variantstudy.model.command.create_renewables_cluster import CreateRenewablesCluster
from antarest.study.storage.variantstudy.model.command_context import CommandContext

# ──────────────────────────────────────────────────────────────────────────────
# Shared tests — run on both database and filesystem backends
# ──────────────────────────────────────────────────────────────────────────────


def test_save_renewable_creates_cluster(dao: StudyDao) -> None:
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
    if isinstance(dao, DatabaseStudyDao):
        assert result == renewable
    else:
        # FS does not normalize the cluster id to lowercase (gap: #TODO)
        assert result.name == renewable.name
        assert result.unit_count == renewable.unit_count
        assert result.nominal_capacity == renewable.nominal_capacity
        assert result.enabled == renewable.enabled

    with pytest.raises(AreaNotFound):
        dao.save_renewable("nonexistent", renewable)


def test_save_renewable_overwrites_existing(dao: StudyDao) -> None:
    dao.save_area("Paris")

    dao.save_renewable("paris", RenewableCluster(id="gas", name="Gas", nominal_capacity=100.0))
    dao.save_renewable("paris", RenewableCluster(id="gas", name="Gas", nominal_capacity=200.0))

    result = dao.get_renewable("paris", "gas")
    assert result.nominal_capacity == 200.0


def test_save_multiple_renewable_clusters(dao: StudyDao) -> None:
    dao.save_area("Paris")

    dao.save_renewables(
        {
            "paris": [
                RenewableCluster(id="battery", name="Battery", nominal_capacity=200.0),
                RenewableCluster(id="solar panels", name="Solar PaNELS", nominal_capacity=500.0),
            ]
        }
    )

    paris_clusters = dao.get_all_renewables_for_area("paris")
    assert len(paris_clusters) == 2
    names = {c.name for c in paris_clusters}
    assert names == {"Battery", "Solar PaNELS"}
    caps = {c.name: c.nominal_capacity for c in paris_clusters}
    assert caps["Battery"] == 200.0
    assert caps["Solar PaNELS"] == 500.0

    # Updates battery and adds wind offshore
    dao.save_renewables(
        {
            "paris": [
                RenewableCluster(id="battery", name="Battery", nominal_capacity=1000.0),
                RenewableCluster(id="wind offshore", name="Wind", nominal_capacity=100.0),
            ]
        }
    )
    paris_clusters = dao.get_all_renewables_for_area("paris")
    assert len(paris_clusters) == 3
    caps2 = {c.name: c.nominal_capacity for c in paris_clusters}
    assert caps2["Battery"] == 1000.0
    assert caps2["Solar PaNELS"] == 500.0
    assert caps2["Wind"] == 100.0

    # Nonexistent area raises
    with pytest.raises(AreaNotFound):
        dao.save_renewables(
            {
                "nonexistent": [
                    RenewableCluster(id="nuclear", name="Nuclear", nominal_capacity=1000.0),
                ]
            }
        )


def test_get_one_renewable_cluster(dao: StudyDao) -> None:
    dao.save_area("Paris")
    dao.save_renewable("paris", RenewableCluster(id="battery", name="Battery"))

    cluster = dao.get_renewable("paris", "battery")
    # FS does not lowercase the cluster id (gap: #TODO)
    assert cluster.id.lower() == "battery"
    assert cluster.name == "Battery"

    with pytest.raises(RenewableClusterNotFound):
        dao.get_renewable("paris", "nonexistent")

    with pytest.raises(AreaNotFound):
        dao.get_renewable("nonexistent", "battery")


def test_get_all_renewables(dao: StudyDao) -> None:
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


def test_delete_renewable(dao: StudyDao) -> None:
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


def test_renewable_exists_returns_false_for_unknown_area(dao: StudyDao) -> None:
    assert not dao.renewable_exists("nonexistent", "gas")


def test_renewable_matrix_round_trip(dao_and_matrix_service) -> None:
    """Matrix survives a save/get round-trip on both backends."""
    dao, matrix_service = dao_and_matrix_service
    dao.save_area("Paris")
    renewable = RenewableCluster(id="battery", name="Battery")
    dao.save_renewable("paris", renewable)

    dataframe = pl.DataFrame(data=[[1, 2.5], [3, 4.7]], orient="row")
    series_id = matrix_service.create(dataframe)

    dao.save_renewable_series({"paris": {"battery": series_id}})
    pl.testing.assert_frame_equal(dao.get_renewable_series("paris", "battery"), dataframe, check_dtypes=False)


def test_area_with_no_clusters_are_absent_from_clusters_dict(dao: StudyDao) -> None:
    dao.save_area("germany")
    dao.save_area("italy")

    dao.save_renewable("germany", RenewableCluster(id="battery", name="Battery"))

    clusters = dao.get_all_renewables()

    assert "italy" not in clusters
    assert "germany" in clusters
    assert "battery" in clusters["germany"]


def test_save_renewable_with_upper_case_name(dao: StudyDao, command_context: CommandContext) -> None:
    dao.save_area("fr")
    command = CreateRenewablesCluster(
        area_id="fr",
        parameters=RenewableClusterCreation(name="MyRenewableCluster"),
        command_context=command_context,
        study_version=dao.get_version(),
    )
    output = command.apply(dao)
    assert output.status  # The command should succeed even if the name is in upper case


# ──────────────────────────────────────────────────────────────────────────────
# DB-only tests — require raw SQL inspection via db_session
# ──────────────────────────────────────────────────────────────────────────────


def test_renewable_series_cascade_delete(db_session: Session, db_dao: DatabaseStudyDao) -> None:
    """Test that renewable series rows are cascade-deleted with the cluster."""
    db_dao.save_area("Paris")
    renewable = RenewableCluster(id="battery", name="Battery")
    db_dao.save_renewable("paris", renewable)

    matrix_service = db_dao._matrix_service
    dataframe = pl.DataFrame(data=[[1, 2.5], [3, 4.7]], orient="row")
    series_id = matrix_service.create(dataframe)

    db_dao.save_renewable_series({"paris": {"battery": series_id}})
    db_dao.delete_renewable("paris", renewable)

    with db_session:
        assert db_session.execute(select(RENEWABLE_CLUSTER_TABLE)).fetchall() == []
        assert db_session.execute(select(RENEWABLE_SERIES_TABLE)).fetchall() == []


def test_get_renewable_matrix_raises_when_missing(db_dao: DatabaseStudyDao) -> None:
    db_dao.save_area("Paris")
    db_dao.save_renewable("paris", RenewableCluster(id="battery", name="Battery"))

    with pytest.raises(RenewableClusterNotFound):
        db_dao.get_renewable_series("paris", "gas")
    with pytest.raises(AreaNotFound):
        db_dao.get_renewable_series("nonexistent", "gas")


def test_save_renewable_matrix_raises_when_missing(db_dao: DatabaseStudyDao) -> None:
    db_dao.save_area("Paris")

    with pytest.raises(RenewableClusterNotFound):
        db_dao.save_renewable_series({"paris": {"gas": "missing-matrix-id"}})
    with pytest.raises(AreaNotFound):
        db_dao.save_renewable_series({"nonexistent": {"gas": "missing-matrix-id"}})
