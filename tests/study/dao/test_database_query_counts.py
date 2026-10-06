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

"""SQL query budgets for collection reads: adding rows must not add round trips."""

from typing import Literal

import pytest
from sqlalchemy.orm import Session

from antarest.study.business.model.renewable_cluster_model import RenewableCluster
from antarest.study.business.model.scenario_builder_model import ScenarioType
from antarest.study.business.model.sts_model import STStorage, initialize_st_storage
from antarest.study.business.model.thermal_cluster_model import ThermalCluster, initialize_thermal_cluster
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from tests.db_statement_recorder import DBStatementRecorder
from tests.study.dao.utils import save_area

ClusterType = Literal["st_storage", "thermal", "renewable"]


def _save_clusters(dao: DatabaseStudyDao, area_id: str, cluster_type: ClusterType, count: int) -> None:
    version = dao.get_version()
    if cluster_type == "st_storage":
        storages = [STStorage(name=f"storage_{i}") for i in range(count)]
        for storage in storages:
            initialize_st_storage(storage, version)
        dao.save_st_storages({area_id: storages})
    elif cluster_type == "thermal":
        thermals = [ThermalCluster(name=f"thermal_{i}") for i in range(count)]
        for thermal in thermals:
            initialize_thermal_cluster(thermal, version)
        dao.save_thermals({area_id: thermals})
    else:
        dao.save_renewables({area_id: [RenewableCluster(name=f"renewable_{i}") for i in range(count)]})


@pytest.mark.parametrize("cluster_type", ["st_storage", "thermal", "renewable"])
@pytest.mark.parametrize("for_area", [False, True], ids=["study", "area"])
@pytest.mark.parametrize("count", [0, 1, 10])
def test_collection_read_query_budget(
    db_dao: DatabaseStudyDao, db_session: Session, cluster_type: ClusterType, for_area: bool, count: int
) -> None:
    save_area(db_dao, "area")
    if count:
        _save_clusters(db_dao, "area", cluster_type, count)

    method_name = {
        "st_storage": "get_all_st_storages",
        "thermal": "get_all_thermals",
        "renewable": "get_all_renewables",
    }[cluster_type]
    if for_area:
        method_name += "_for_area"
    read = getattr(db_dao, method_name)

    with DBStatementRecorder(db_session.get_bind()) as recorder:
        result = read("area") if for_area else read()

    actual_count = len(result) if for_area else sum(len(items) for items in result.values())
    assert actual_count == count
    budget = 1  # Read the collection, even when it is empty.
    if count > 0:
        # Only nonempty collections need the study version to convert the rows.
        budget += 1
    if for_area and (count == 0 or cluster_type == "renewable"):
        # The renewable DAO always validates the area before reading its clusters.
        # The thermal and storage DAOs only validate it when no rows are found.
        # This reflects the existing DAO behavior, independently of version reads.
        budget += 1
    assert len(recorder.sql_statements) <= budget, str(recorder)


def test_storage_scenario_query_count_does_not_grow_with_areas_or_storages(
    db_dao_930: DatabaseStudyDao, db_session: Session
) -> None:
    save_area(db_dao_930, "area_0")
    _save_clusters(db_dao_930, "area_0", "st_storage", 1)
    with DBStatementRecorder(db_session.get_bind()) as small:
        small_result = db_dao_930.get_scenario_by_type(ScenarioType.SHORT_TERM_STORAGE_INFLOWS)
    assert set(small_result["area_0"]) == {"storage_0"}

    for i in range(5):
        area_id = f"area_{i}"
        if i:
            save_area(db_dao_930, area_id)
        _save_clusters(db_dao_930, area_id, "st_storage", 10)

    with DBStatementRecorder(db_session.get_bind()) as large:
        large_result = db_dao_930.get_scenario_by_type(ScenarioType.SHORT_TERM_STORAGE_INFLOWS)
    assert set(large_result) == {f"area_{i}" for i in range(5)}
    assert all(set(storages) == {f"storage_{i}" for i in range(10)} for storages in large_result.values())
    assert len(large.sql_statements) <= len(small.sql_statements), str(large)
