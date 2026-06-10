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

from antarest.core.exceptions import AreaNotFound, RenewableClusterNotFound
from antarest.study.business.model.renewable_cluster_model import (
    RenewableCluster,
    RenewableClusterCreation,
    RenewableClusterGroup,
    TimeSeriesInterpretation,
)
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.storage.variantstudy.model.command.create_renewables_cluster import CreateRenewablesCluster
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from tests.study.dao.utils import save_area


def test_save_renewable_creates_cluster(dao: StudyDao) -> None:
    save_area(dao, "Paris")

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
        # Intentional divergence: FS keeps the original case to stay backward-compatible
        # with existing studies on disk (see backward-compat note in renewable_cluster_model.py:90-96);
        # DB normalizes to lowercase since it only stores new studies.
        assert result.name == renewable.name
        assert result.unit_count == renewable.unit_count
        assert result.nominal_capacity == renewable.nominal_capacity
        assert result.enabled == renewable.enabled

    with pytest.raises(AreaNotFound):
        dao.save_renewable("nonexistent", renewable)


def test_save_renewable_overwrites_existing(dao: StudyDao) -> None:
    save_area(dao, "Paris")

    dao.save_renewable("paris", RenewableCluster(id="gas", name="Gas", nominal_capacity=100.0))
    dao.save_renewable("paris", RenewableCluster(id="gas", name="Gas", nominal_capacity=200.0))

    result = dao.get_renewable("paris", "gas")
    assert result.nominal_capacity == 200.0


def test_save_multiple_renewable_clusters(dao: StudyDao) -> None:
    save_area(dao, "Paris")

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
                    RenewableCluster(id="fuel", name="Fuel", nominal_capacity=100.0),
                ]
            }
        )


def test_get_one_renewable_cluster(dao: StudyDao) -> None:
    save_area(dao, "Paris")

    dao.save_renewable("paris", RenewableCluster(id="battery", name="Battery"))

    cluster = dao.get_renewable("paris", "battery")
    # Intentional divergence: FS keeps the original case for backward compatibility
    # with existing studies on disk; DB normalizes to lowercase.
    # Compare case-insensitively to assert both backends.
    assert cluster.id.lower() == "battery"
    assert cluster.name == "Battery"

    with pytest.raises(RenewableClusterNotFound):
        dao.get_renewable("paris", "nonexistent")

    with pytest.raises(AreaNotFound):
        dao.get_renewable("nonexistent", "battery")


def test_get_all_renewables(dao: StudyDao) -> None:
    save_area(dao, "Paris")
    save_area(dao, "London")

    dao.save_renewable("paris", RenewableCluster(id="battery", name="Battery"))
    dao.save_renewable("london", RenewableCluster(id="wind", name="Wind"))

    all_renewables = dao.get_all_renewables()
    assert set(all_renewables.keys()) == {"paris", "london"}
    assert set(all_renewables["paris"].keys()) == {"battery"}
    assert set(all_renewables["london"].keys()) == {"wind"}

    with pytest.raises(AreaNotFound):
        dao.get_all_renewables_for_area("nonexistent")


def test_delete_renewable(dao: StudyDao) -> None:
    save_area(dao, "Paris")

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
    save_area(dao, "Paris")
    renewable = RenewableCluster(id="battery", name="Battery")
    dao.save_renewable("paris", renewable)

    dataframe = pl.DataFrame(data=[[1, 2.5], [3, 4.7]], orient="row")
    series_id = matrix_service.create(dataframe)

    dao.save_renewable_series({"paris": {"battery": series_id}})
    pl.testing.assert_frame_equal(dao.get_renewable_series("paris", "battery"), dataframe, check_dtypes=False)

    dao.delete_renewable("paris", renewable)

    assert dao.get_all_renewables() == {}
    assert dao.get_all_renewables_series() == {}


def test_get_renewable_matrix_raises_when_missing(dao: StudyDao) -> None:
    save_area(dao, "Paris")
    dao.save_renewable("paris", RenewableCluster(id="battery", name="Battery"))

    with pytest.raises(RenewableClusterNotFound):
        dao.get_renewable_series("paris", "gas")
    with pytest.raises(AreaNotFound):
        dao.get_renewable_series("nonexistent", "gas")


def test_save_renewable_matrix_raises_when_missing(dao: StudyDao) -> None:
    save_area(dao, "Paris")

    with pytest.raises(RenewableClusterNotFound):
        dao.save_renewable_series({"paris": {"gas": "missing-matrix-id"}})
    with pytest.raises(AreaNotFound):
        dao.save_renewable_series({"nonexistent": {"gas": "missing-matrix-id"}})


def test_area_with_no_clusters_are_absent_from_clusters_dict(dao: StudyDao) -> None:
    save_area(dao, "germany")
    save_area(dao, "italy")

    dao.save_renewable("germany", RenewableCluster(id="battery", name="Battery"))

    clusters = dao.get_all_renewables()

    assert "italy" not in clusters
    assert "germany" in clusters
    assert "battery" in clusters["germany"]


def test_save_renewable_with_upper_case_name(dao: StudyDao, command_context: CommandContext) -> None:
    save_area(dao, "fr")
    command = CreateRenewablesCluster(
        area_id="fr",
        parameters=RenewableClusterCreation(name="MyRenewableCluster"),
        command_context=command_context,
        study_version=dao.get_version(),
    )
    output = command.apply(dao)
    assert output.status  # The command should succeed even if the name is in upper case
