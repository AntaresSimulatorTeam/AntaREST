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
import polars as pl
import pytest

from antarest.core.exceptions import AreaNotFound, ReserveDefinitionNotFound
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.business.model.reserve_definition_model import (
    ReserveDefinition,
    ReserveDefinitionId,
    ReserveType,
)
from antarest.study.dao.api.study_dao import StudyDao
from tests.study.dao.utils import save_area


def _reserve(id_: str, reserve_type: ReserveType = ReserveType.UP, **overrides) -> ReserveDefinition:
    base = dict(
        id=id_,
        type=reserve_type,
        failure_cost=10.0,
        spillage_cost=5.0,
        reference_activation_duration=3,
        power_activation_ratio=0.4,
        energy_activation_ratio=0.9,
    )
    base.update(overrides)
    return ReserveDefinition(**base)


def test_save_and_retrieve(dao_10_0: StudyDao) -> None:
    save_area(dao_10_0, "paris")

    reserve = _reserve("Reserve 1")
    dao_10_0.save_reserve_definitions({"paris": [reserve]})

    fetched = dao_10_0.get_reserve_definition("paris", reserve.id)
    assert fetched == reserve


def test_save_updates_existing(dao_10_0: StudyDao) -> None:
    save_area(dao_10_0, "paris")

    dao_10_0.save_reserve_definitions({"paris": [_reserve("R1", failure_cost=10.0)]})
    dao_10_0.save_reserve_definitions({"paris": [_reserve("R1", failure_cost=999.0)]})

    fetched = dao_10_0.get_reserve_definition("paris", "R1")
    assert fetched.failure_cost == 999.0


def test_save_raises_area_not_found_when_area_missing(dao_10_0: StudyDao) -> None:
    with pytest.raises(AreaNotFound):
        dao_10_0.save_reserve_definitions({"nonexistent": [_reserve("R1")]})


def test_reserve_definition_exists(dao_10_0: StudyDao) -> None:
    save_area(dao_10_0, "paris")
    dao_10_0.save_reserve_definitions({"paris": [_reserve("R1")]})

    assert dao_10_0.reserve_definition_exists("paris", "R1") is True
    assert dao_10_0.reserve_definition_exists("paris", "unknown") is False


def test_reserve_definition_exists_on_missing_area(dao_10_0: StudyDao) -> None:
    assert dao_10_0.reserve_definition_exists("nonexistent", "r1") is False


def test_get_raises_area_not_found(dao_10_0: StudyDao) -> None:
    with pytest.raises(AreaNotFound):
        dao_10_0.get_reserve_definition("nonexistent", "r1")


def test_get_raises_reserve_not_found_when_area_exists(dao_10_0: StudyDao) -> None:
    save_area(dao_10_0, "paris")
    with pytest.raises(ReserveDefinitionNotFound):
        dao_10_0.get_reserve_definition("paris", "unknown")


def test_get_all_for_area(dao_10_0: StudyDao) -> None:
    save_area(dao_10_0, "paris")
    dao_10_0.save_reserve_definitions({"paris": [_reserve("R1"), _reserve("R2", ReserveType.DOWN)]})

    fetched = list(dao_10_0.get_all_reserve_definitions_for_area("paris"))
    assert len(fetched) == 2
    assert {r.id for r in fetched} == {"R1", "R2"}


def test_get_all_for_area_empty(dao_10_0: StudyDao) -> None:
    save_area(dao_10_0, "paris")
    assert list(dao_10_0.get_all_reserve_definitions_for_area("paris")) == []


def test_get_all_for_area_raises_area_not_found(dao_10_0: StudyDao) -> None:
    with pytest.raises(AreaNotFound):
        list(dao_10_0.get_all_reserve_definitions_for_area("nonexistent"))


def test_get_all_across_areas(dao_10_0: StudyDao) -> None:
    save_area(dao_10_0, "paris")
    save_area(dao_10_0, "lyon")

    dao_10_0.save_reserve_definitions(
        {
            "paris": [_reserve("R1"), _reserve("R2", ReserveType.DOWN)],
            "lyon": [_reserve("R1")],
        }
    )

    result = dao_10_0.get_all_reserve_definitions()
    assert set(result.keys()) == {"paris", "lyon"}
    assert set(result["paris"].keys()) == {"R1", "R2"}
    assert set(result["lyon"].keys()) == {"R1"}


def test_delete(dao_10_0: StudyDao) -> None:
    save_area(dao_10_0, "paris")
    dao_10_0.save_reserve_definitions({"paris": [_reserve("R1"), _reserve("R2")]})

    dao_10_0.delete_reserve_definitions("paris", ["R1"])

    assert dao_10_0.reserve_definition_exists("paris", "R1") is False
    assert dao_10_0.reserve_definition_exists("paris", "R2") is True


def test_delete_not_found_raises(dao_10_0: StudyDao) -> None:
    save_area(dao_10_0, "paris")
    with pytest.raises(ReserveDefinitionNotFound):
        dao_10_0.delete_reserve_definitions("paris", ["unknown"])


def test_save_and_retrieve_reserve_need(dao_10_0: StudyDao, matrix_service: ISimpleMatrixService) -> None:
    save_area(dao_10_0, "paris")
    dao_10_0.save_reserve_definitions({"paris": [_reserve("R1")]})

    matrix_df = pl.DataFrame([[0.0]] * 8760, orient="row")
    matrix_id = matrix_service.create(matrix_df)
    dao_10_0.save_reserve_need({"paris": {ReserveDefinitionId("R1"): matrix_id}})

    fetched = dao_10_0.get_reserve_need("paris", "R1")
    assert fetched.shape == (8760, 1)


def test_get_all_reserve_needs_empty(dao_10_0: StudyDao) -> None:
    save_area(dao_10_0, "paris")
    assert dao_10_0.get_all_reserve_needs() == {}


def test_delete_reserve_need(dao_10_0: StudyDao, matrix_service: ISimpleMatrixService) -> None:
    save_area(dao_10_0, "paris")
    dao_10_0.save_reserve_definitions({"paris": [_reserve("R1")]})
    reserve_id = ReserveDefinitionId("R1")
    matrix_id = matrix_service.create(pl.DataFrame([[0.0]] * 8760, orient="row"))
    dao_10_0.save_reserve_need({"paris": {reserve_id: matrix_id}})

    dao_10_0.delete_reserve_need("paris", reserve_id)
    assert dao_10_0.get_all_reserve_needs().get("paris", {}).get(reserve_id) is None
