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
from sqlalchemy import select
from sqlalchemy.orm import Session

from antarest.core.exceptions import AreaNotFound, ReserveDefinitionNotFound
from antarest.study.business.model.reserve_definition_model import ReserveDefinition, ReserveType
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.dao.database.models.reserve_definition import RESERVE_DEFINITION_TABLE
from tests.study.dao.utils import save_area


def _reserve(name: str, reserve_type: ReserveType = ReserveType.UP, **overrides) -> ReserveDefinition:
    base = dict(
        name=name,
        type=reserve_type,
        failure_cost=10.0,
        spillage_cost=5.0,
        reference_activation_duration=3,
        power_activation_ratio=0.4,
        energy_activation_ratio=0.9,
    )
    base.update(overrides)
    return ReserveDefinition(**base)


def test_get_raises_when_area_does_not_exist(db_dao: DatabaseStudyDao) -> None:
    with pytest.raises(AreaNotFound):
        db_dao.get_reserve_definition("nonexistent", "R1")


def test_get_raises_reserve_not_found_when_area_exists(db_dao: DatabaseStudyDao) -> None:
    save_area(db_dao, "paris")
    with pytest.raises(ReserveDefinitionNotFound):
        db_dao.get_reserve_definition("paris", "unknown")


def test_get_all_empty_area_raises_area_not_found_when_area_missing(db_dao: DatabaseStudyDao) -> None:
    with pytest.raises(AreaNotFound):
        list(db_dao.get_all_reserve_definitions_for_area("nonexistent"))


def test_save_and_retrieve(db_dao: DatabaseStudyDao) -> None:
    save_area(db_dao, "paris")

    reserve = _reserve("Reserve 1")
    db_dao.save_reserve_definitions({"paris": [reserve]})

    fetched = db_dao.get_reserve_definition("paris", reserve.id)
    assert fetched == reserve


def test_save_updates_existing(db_dao: DatabaseStudyDao) -> None:
    save_area(db_dao, "paris")

    db_dao.save_reserve_definitions({"paris": [_reserve("R1", failure_cost=10.0)]})
    db_dao.save_reserve_definitions({"paris": [_reserve("R1", failure_cost=999.0)]})

    fetched = db_dao.get_reserve_definition("paris", "R1")
    assert fetched.failure_cost == 999.0


def test_reserve_definition_exists(db_dao: DatabaseStudyDao) -> None:
    save_area(db_dao, "paris")
    db_dao.save_reserve_definitions({"paris": [_reserve("R1")]})

    assert db_dao.reserve_definition_exists("paris", "R1") is True
    assert db_dao.reserve_definition_exists("paris", "unknown") is False


def test_get_all_across_areas(db_dao: DatabaseStudyDao) -> None:
    save_area(db_dao, "paris")
    save_area(db_dao, "lyon")

    db_dao.save_reserve_definitions(
        {
            "paris": [_reserve("R1"), _reserve("R2", ReserveType.DOWN)],
            "lyon": [_reserve("R1")],
        }
    )

    result = db_dao.get_all_reserve_definitions()
    assert set(result.keys()) == {"paris", "lyon"}
    assert set(result["paris"].keys()) == {"R1", "R2"}
    assert set(result["lyon"].keys()) == {"R1"}


def test_get_all_for_area(db_dao: DatabaseStudyDao) -> None:
    save_area(db_dao, "paris")
    db_dao.save_reserve_definitions({"paris": [_reserve("R1"), _reserve("R2", ReserveType.DOWN)]})
    fetched = list(db_dao.get_all_reserve_definitions_for_area("paris"))
    assert len(fetched) == 2
    assert {r.id for r in fetched} == {"R1", "R2"}


def test_delete(db_dao: DatabaseStudyDao) -> None:
    save_area(db_dao, "paris")
    db_dao.save_reserve_definitions({"paris": [_reserve("R1"), _reserve("R2")]})

    db_dao.delete_reserve_definition("paris", "R1")

    assert db_dao.reserve_definition_exists("paris", "R1") is False
    assert db_dao.reserve_definition_exists("paris", "R2") is True


def test_delete_not_found_raises(db_dao: DatabaseStudyDao) -> None:
    save_area(db_dao, "paris")
    with pytest.raises(ReserveDefinitionNotFound):
        db_dao.delete_reserve_definition("paris", "unknown")


def test_cascade_delete_on_area_removal(db_session: Session, db_dao: DatabaseStudyDao) -> None:
    save_area(db_dao, "paris")
    db_dao.save_reserve_definitions({"paris": [_reserve("R1")]})

    with db_session:
        db_dao.delete_area("paris")
        rows = db_session.execute(select(RESERVE_DEFINITION_TABLE)).fetchall()
        assert rows == []
