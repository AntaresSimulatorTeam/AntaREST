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


import pytest
from pytest_mock import MockerFixture
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.business.model.gems.catalog import GemsCatalog
from antarest.study.dao.database.models import STUDY_DATA_TABLE
from antarest.study.dao.database.models.gems.catalog import GEMS_CATALOG_METRICS_TABLE, GEMS_CATALOGS_TABLE
from tests.study.dao.conftest import assert_catalogs_equal, build_db_dao_10_2, prepare_catalog_taxonomy


def test_catalogs_are_isolated_and_deleted_with_study(
    db_session: Session, matrix_service: ISimpleMatrixService, gems_catalog: GemsCatalog
) -> None:
    first = build_db_dao_10_2(db_session, matrix_service)
    prepare_catalog_taxonomy(first)
    second = build_db_dao_10_2(db_session, matrix_service)
    prepare_catalog_taxonomy(second, "another_taxonomy")
    other_catalog = gems_catalog.model_copy(update={"taxonomy": "another_taxonomy"})
    first.save_catalogs([gems_catalog])
    second.save_catalogs([other_catalog])
    assert_catalogs_equal(first.get_catalogs(), [gems_catalog])
    assert_catalogs_equal(second.get_catalogs(), [other_catalog])

    first_study_data_id = db_session.scalar(
        select(STUDY_DATA_TABLE.c.study_data_id).where(STUDY_DATA_TABLE.c.study_id == first.get_study_id())
    )
    db_session.execute(delete(STUDY_DATA_TABLE).where(STUDY_DATA_TABLE.c.study_data_id == first_study_data_id))
    db_session.commit()
    assert first.get_catalogs() == []
    assert_catalogs_equal(second.get_catalogs(), [other_catalog])
    assert db_session.execute(select(GEMS_CATALOGS_TABLE)).one().taxonomy == "another_taxonomy"
    remaining_metrics = db_session.execute(select(GEMS_CATALOG_METRICS_TABLE)).all()
    assert len(remaining_metrics) == len(other_catalog.metrics_definition)
    assert all(row.study_data_id != first_study_data_id for row in remaining_metrics)


@pytest.mark.parametrize("catalog_count", [1, 5])
def test_catalog_batch_uses_grouped_queries(
    db_session: Session,
    matrix_service: ISimpleMatrixService,
    gems_catalog: GemsCatalog,
    mocker: MockerFixture,
    catalog_count: int,
) -> None:
    dao = build_db_dao_10_2(db_session, matrix_service)
    prepare_catalog_taxonomy(dao)
    execute = mocker.spy(db_session, "execute")
    commit = mocker.spy(db_session, "commit")
    catalogs = [gems_catalog.model_copy(update={"id": f"catalog_{i}"}) for i in range(catalog_count)]
    dao.save_catalogs(catalogs)
    # One duplicate check and two bulk inserts, regardless of the number of catalogs/metrics.
    assert execute.call_count == 3
    assert commit.call_count == 1
    execute.reset_mock()
    assert_catalogs_equal(dao.get_catalogs(), catalogs)
    assert execute.call_count == 2
    execute.reset_mock()
    commit.reset_mock()
    dao.save_catalogs([])
    execute.assert_not_called()
    commit.assert_not_called()


def test_catalog_batch_rolls_back_on_metric_insert_failure(
    db_session: Session, matrix_service: ISimpleMatrixService, gems_catalog: GemsCatalog
) -> None:
    dao = build_db_dao_10_2(db_session, matrix_service)
    prepare_catalog_taxonomy(dao)
    # Bypass Pydantic validation to exercise the DB constraint and rollback after catalog insertion.
    metric = gems_catalog.metrics_definition[0]
    invalid = gems_catalog.model_copy(update={"id": "invalid", "metrics_definition": [metric, metric]})
    with pytest.raises(IntegrityError):
        dao.save_catalogs([gems_catalog, invalid])
    assert dao.get_catalogs() == []
    assert db_session.execute(select(GEMS_CATALOG_METRICS_TABLE)).all() == []
    dao.save_catalogs([gems_catalog])
    assert_catalogs_equal(dao.get_catalogs(), [gems_catalog])


def test_catalog_location_must_exist_in_same_study(
    db_session: Session, matrix_service: ISimpleMatrixService, gems_catalog: GemsCatalog
) -> None:
    first = build_db_dao_10_2(db_session, matrix_service)
    second = build_db_dao_10_2(db_session, matrix_service)
    prepare_catalog_taxonomy(first)
    with pytest.raises(IntegrityError):
        second.save_catalogs([gems_catalog])
    assert second.get_catalogs() == []
    prepare_catalog_taxonomy(second)
    second.save_catalogs([gems_catalog])
    saved = second.get_catalogs()
    assert_catalogs_equal(saved, [gems_catalog])
    assert [metric.id for metric in saved[0].metrics_definition] == sorted(
        metric.id for metric in gems_catalog.metrics_definition
    )


@pytest.mark.parametrize("taxonomy_id", ["missing_taxonomy", "other_study_taxonomy"])
def test_catalog_taxonomy_must_match_its_study(
    db_session: Session, matrix_service: ISimpleMatrixService, gems_catalog: GemsCatalog, taxonomy_id: str
) -> None:
    dao = build_db_dao_10_2(db_session, matrix_service)
    prepare_catalog_taxonomy(dao)
    other_dao = build_db_dao_10_2(db_session, matrix_service)
    prepare_catalog_taxonomy(other_dao, "other_study_taxonomy")
    invalid = gems_catalog.model_copy(update={"id": "invalid", "taxonomy": taxonomy_id})
    with pytest.raises(IntegrityError):
        dao.save_catalogs([gems_catalog, invalid])
    assert dao.get_catalogs() == []
    dao.save_catalogs([gems_catalog])
    assert_catalogs_equal(dao.get_catalogs(), [gems_catalog])
