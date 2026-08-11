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
Behaviour of the surrogate study key the database DAOs are built on.

The study data tables are keyed by `study_data.study_data_id`, a generated bigint, while the
rest of the application knows studies by their 36 chars id. These tests cover the translation
between the two: it must resolve to the right study, isolate studies from one another, and never
outlive the `study_data` row it was read from.
"""

import uuid

import pytest
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from antarest.blobstore.in_memory import InMemoryBlobService
from antarest.core.exceptions import StudyNotFoundError
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.business.model.area_properties_model import AreaProperties
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.dao.database.database_study_factory_dao import DatabaseStudyDaoFactory
from antarest.study.dao.database.models import STUDY_DATA_TABLE
from antarest.study.dao.database.models.area import AREA_TABLE
from antarest.study.model import STUDY_VERSION_8_8, StorageMode, Study, StudyMetadataCreation
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from tests.conftest import build_db_dao
from tests.helpers import create_study


def _build_factory(db_session: Session, matrix_service: ISimpleMatrixService) -> DatabaseStudyDaoFactory:
    generator_matrix_constants = GeneratorMatrixConstants(matrix_service)
    generator_matrix_constants.init_constant_matrices()
    return DatabaseStudyDaoFactory(matrix_service, InMemoryBlobService(), generator_matrix_constants, db_session)


def _stored_study_data_id(db_session: Session, study_id: str) -> int:
    stmt = select(STUDY_DATA_TABLE.c.study_data_id).where(STUDY_DATA_TABLE.c.study_id == study_id)
    study_data_id: int = db_session.execute(stmt).scalar_one()
    return study_data_id


def test_study_id_stays_the_string_id(db_dao: DatabaseStudyDao, db_session: Session) -> None:
    """
    `get_study_id()` is public API used all over the application: the surrogate key must not
    leak through it.
    """
    study_id = db_dao.get_study_id()

    assert isinstance(study_id, str)
    assert db_session.get(Study, study_id) is not None


def test_study_data_id_is_resolved_from_the_database(db_session: Session, matrix_service: ISimpleMatrixService) -> None:
    """
    A DAO obtained for an existing study — the read path, as opposed to study creation — resolves
    its key by looking it up.
    """
    created = build_db_dao(db_session, matrix_service, STUDY_VERSION_8_8)
    study_id = created.get_study_id()

    dao = _build_factory(db_session, matrix_service).get_study_dao(study_id, True)

    assert dao._study_data_id == _stored_study_data_id(db_session, study_id)


def test_resolution_fails_for_a_study_without_data(db_session: Session, matrix_service: ISimpleMatrixService) -> None:
    """
    A study whose data was cleared has no `study_data` row. Querying it must fail loudly rather
    than silently match nothing.
    """
    study_id = str(uuid.uuid4())
    with db_session:
        study = create_study(id=study_id, name="No data", version=str(STUDY_VERSION_8_8))
        study.storage_mode = StorageMode.DATABASE
        db_session.add(study)
        db_session.commit()

    dao = _build_factory(db_session, matrix_service).get_study_dao(study_id, True)

    with pytest.raises(StudyNotFoundError):
        dao.get_all_area_ids()


def test_studies_do_not_see_each_other_data(db_session: Session, matrix_service: ISimpleMatrixService) -> None:
    """
    The whole point of the key swap is that every data row carries the study it belongs to. Two
    studies sharing a table must not read each other's rows.
    """
    first = build_db_dao(db_session, matrix_service, STUDY_VERSION_8_8)
    second = build_db_dao(db_session, matrix_service, STUDY_VERSION_8_8)

    first.save_areas_with_properties({"fr": AreaProperties()})
    second.save_areas_with_properties({"de": AreaProperties(), "es": AreaProperties()})

    assert set(first.get_all_area_ids()) == {"fr"}
    assert set(second.get_all_area_ids()) == {"de", "es"}

    first_id = _stored_study_data_id(db_session, first.get_study_id())
    second_id = _stored_study_data_id(db_session, second.get_study_id())
    assert first_id != second_id

    stored = db_session.execute(select(AREA_TABLE.c.study_data_id, AREA_TABLE.c.area_id)).fetchall()
    assert sorted(stored) == sorted([(first_id, "fr"), (second_id, "de"), (second_id, "es")])


def test_two_studies_can_hold_the_same_area_id(db_session: Session, matrix_service: ISimpleMatrixService) -> None:
    """
    Every write goes through `upsert_multiple`, whose conflict target is the primary key of the
    table — now led by `study_data_id`. Were the study left out of it, saving an area in one study
    would overwrite the area of the same name in another.
    """
    first = build_db_dao(db_session, matrix_service, STUDY_VERSION_8_8)
    second = build_db_dao(db_session, matrix_service, STUDY_VERSION_8_8)

    first.save_areas_with_properties({"fr": AreaProperties(energy_cost_unsupplied=1.0)})
    second.save_areas_with_properties({"fr": AreaProperties(energy_cost_unsupplied=2.0)})

    assert first.get_all_area_ids() == ["fr"]
    assert second.get_all_area_ids() == ["fr"]
    assert first.get_area_properties("fr").energy_cost_unsupplied == 1.0
    assert second.get_area_properties("fr").energy_cost_unsupplied == 2.0


def test_deleting_a_study_clears_its_data_only(db_session: Session, matrix_service: ISimpleMatrixService) -> None:
    first = build_db_dao(db_session, matrix_service, STUDY_VERSION_8_8)
    second = build_db_dao(db_session, matrix_service, STUDY_VERSION_8_8)
    first.save_areas_with_properties({"fr": AreaProperties()})
    second.save_areas_with_properties({"de": AreaProperties()})
    second_id = _stored_study_data_id(db_session, second.get_study_id())

    with db_session:
        db_session.delete(db_session.get(Study, first.get_study_id()))
        db_session.commit()

    with db_session:
        remaining_studies = db_session.execute(select(STUDY_DATA_TABLE.c.study_id)).scalars().all()
        assert remaining_studies == [second.get_study_id()]
        remaining_areas = db_session.execute(select(AREA_TABLE.c.study_data_id, AREA_TABLE.c.area_id)).fetchall()
        assert [tuple(row) for row in remaining_areas] == [(second_id, "de")]


def test_recreated_study_data_gets_a_new_key(db_session: Session, matrix_service: ISimpleMatrixService) -> None:
    """
    Clearing a study's data and re-extracting it (unarchive, snapshot regeneration, ...) deletes
    the `study_data` row and inserts a new one. The DAO caches its key, so it must not be reused
    across that: this test pins the invariant every such path relies on — a DAO built afterwards
    reads the key of the new row, and the data of the previous incarnation is gone.
    """
    factory = _build_factory(db_session, matrix_service)
    dao = build_db_dao(db_session, matrix_service, STUDY_VERSION_8_8)
    study_id = dao.get_study_id()
    dao.save_areas_with_properties({"fr": AreaProperties()})
    initial_id = _stored_study_data_id(db_session, study_id)

    # What `remove_study_data` does, followed by a re-extraction.
    with db_session:
        db_session.execute(delete(STUDY_DATA_TABLE).where(STUDY_DATA_TABLE.c.study_id == study_id))
        db_session.commit()
    recreated = factory.create_study_dao(StudyMetadataCreation(id=study_id, version=STUDY_VERSION_8_8, managed=True))

    new_id = _stored_study_data_id(db_session, study_id)
    assert recreated._study_data_id == new_id
    # The data of the previous incarnation went away with its `study_data` row.
    assert recreated.get_all_area_ids() == []
    # A DAO built after the fact reads the new key, whether or not the value changed: SQLite
    # reuses the freed rowid, PostgreSQL takes the next value of its sequence.
    assert factory.get_study_dao(study_id, True)._study_data_id == new_id
    # The hazard this guards against: the DAO of the previous incarnation still holds the key it
    # resolved. It is only harmless because no caller keeps one across a re-extraction.
    assert dao._study_data_id == initial_id
