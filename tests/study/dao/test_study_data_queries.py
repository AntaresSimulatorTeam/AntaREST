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
Cross-study queries on the study data tables, used by the garbage collectors.

These are the two places that read the study data tables from outside a `DatabaseStudyDao`, and
they decide what gets deleted: a matrix or a blob missing from their listing is collected. Since
the tables are now keyed by `study_data_id`, both have to join back through `study_data`, and a
join that drops rows silently destroys data that is still in use.
"""

from pathlib import PurePosixPath

import polars as pl
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.business.model.area_properties_model import AreaProperties
from antarest.study.business.model.user_model import ResourceType, UserResourceDataCreation
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.dao.database.models import STUDY_DATA_TABLE
from antarest.study.dao.database.models.area import LOAD_TABLE, SOLAR_TABLE
from antarest.study.dao.database.study_data_queries import belongs_to_study, yield_matrix_ids, yield_used_blobs
from antarest.study.model import STUDY_VERSION_8_8
from tests.conftest import build_db_dao


def _save_load_and_solar(dao: DatabaseStudyDao, area_id: str) -> tuple[str, str]:
    """Give a study one `load` and one `solar` matrix, and return their ids."""
    dao.save_areas_with_properties({area_id: AreaProperties()})
    load_id = dao.matrix_service.create(pl.DataFrame(data=[[1.0], [2.0]], orient="row"))
    solar_id = dao.matrix_service.create(pl.DataFrame(data=[[3.0], [4.0]], orient="row"))
    dao.save_load({area_id: load_id})
    dao.save_solar({area_id: solar_id})
    return load_id, solar_id


def test_matrix_usage_is_scoped_to_one_study(db_session: Session, matrix_service: ISimpleMatrixService) -> None:
    """
    The matrix garbage collector asks for the matrices of one study at a time. Returning another
    study's matrices would keep dead matrices alive; missing one would delete a live matrix.
    """
    first = build_db_dao(db_session, matrix_service, STUDY_VERSION_8_8)
    second = build_db_dao(db_session, matrix_service, STUDY_VERSION_8_8)
    first_load, first_solar = _save_load_and_solar(first, "fr")
    second_load, second_solar = _save_load_and_solar(second, "de")

    tables = [LOAD_TABLE, SOLAR_TABLE]
    first_usage = set(yield_matrix_ids(db_session, tables, first.get_study_id()))
    second_usage = set(yield_matrix_ids(db_session, tables, second.get_study_id()))

    assert first_usage == {(LOAD_TABLE, first_load), (SOLAR_TABLE, first_solar)}
    assert second_usage == {(LOAD_TABLE, second_load), (SOLAR_TABLE, second_solar)}


def test_matrix_usage_of_an_unknown_study_is_empty(db_session: Session, matrix_service: ISimpleMatrixService) -> None:
    """
    A study with no `study_data` row has no data left to reference matrices, so reporting none is
    the right answer — and the one that lets the collector reclaim them.
    """
    dao = build_db_dao(db_session, matrix_service, STUDY_VERSION_8_8)
    _save_load_and_solar(dao, "fr")

    with db_session:
        db_session.execute(delete(STUDY_DATA_TABLE).where(STUDY_DATA_TABLE.c.study_id == dao.get_study_id()))
        db_session.commit()

    assert list(yield_matrix_ids(db_session, [LOAD_TABLE, SOLAR_TABLE], dao.get_study_id())) == []
    assert list(yield_matrix_ids(db_session, [LOAD_TABLE, SOLAR_TABLE], "never-existed")) == []


def test_belongs_to_study_selects_the_rows_of_one_study(
    db_session: Session, matrix_service: ISimpleMatrixService
) -> None:
    first = build_db_dao(db_session, matrix_service, STUDY_VERSION_8_8)
    second = build_db_dao(db_session, matrix_service, STUDY_VERSION_8_8)
    _save_load_and_solar(first, "fr")
    _save_load_and_solar(second, "de")

    stmt = select(LOAD_TABLE.c.area_id).where(belongs_to_study(LOAD_TABLE, first.get_study_id()))

    assert db_session.execute(stmt).scalars().all() == ["fr"]


def test_used_blobs_are_attributed_to_their_study(db_session: Session, matrix_service: ISimpleMatrixService) -> None:
    """
    The blob garbage collector walks every study at once, and each blob is reported along with the
    study using it. A join losing rows would collect blobs that are still referenced.
    """
    first = build_db_dao(db_session, matrix_service, STUDY_VERSION_8_8)
    second = build_db_dao(db_session, matrix_service, STUDY_VERSION_8_8)
    first.save_user_resources(
        [UserResourceDataCreation(path=PurePosixPath("a.txt"), resource_type=ResourceType.FILE, blob_id="blob_a")]
    )
    second.save_user_resources(
        [
            UserResourceDataCreation(path=PurePosixPath("b.txt"), resource_type=ResourceType.FILE, blob_id="blob_b"),
            UserResourceDataCreation(path=PurePosixPath("folder"), resource_type=ResourceType.FOLDER),
        ]
    )

    assert set(yield_used_blobs(db_session)) == {
        ("blob_a", first.get_study_id()),
        ("blob_b", second.get_study_id()),
    }
