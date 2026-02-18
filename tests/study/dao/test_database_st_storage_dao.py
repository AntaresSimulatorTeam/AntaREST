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
Unit tests for DatabaseStStorageDao.
"""

import polars as pl
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from antarest.core.exceptions import STStorageAdditionalConstraintNotFound, STStorageNotFound
from antarest.study.business.model.sts_model import STStorage, STStorageAdditionalConstraint
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.dao.database.models.st_storage import (
    COST_INJECTION_TABLE,
    COST_LEVEL_TABLE,
    COST_VARIATION_INJECTION_TABLE,
    COST_VARIATION_WITHDRAWAL_TABLE,
    COST_WITHDRAWAL_TABLE,
    INFLOWS_TABLE,
    LOWER_RULE_CURVE_TABLE,
    PMAX_INJECTION_TABLE,
    PMAX_WITHDRAWAL_TABLE,
    ST_STORAGE_ADDITIONAL_CONSTRAINT_MATRIX_TABLE,
    ST_STORAGE_ADDITIONAL_CONSTRAINT_TABLE,
    ST_STORAGE_TABLE,
    UPPER_RULE_CURVE_TABLE,
)


def test_save_st_storage(dao: DatabaseStudyDao) -> None:
    dao.save_area("area_1")

    dao.save_st_storage("area_1", STStorage(id="st_storage_id", name="st-storage", efficiency=0.8))

    st_storage = dao.get_st_storage("area_1", "st_storage_id")
    assert st_storage.id == "st_storage_id"
    assert st_storage.name == "st-storage"
    assert st_storage.efficiency == 0.8

    with pytest.raises(STStorageNotFound):
        dao.save_st_storage("nonexistent", STStorage(id="st_storage_id", name="st-storage"))


def test_save_multiple_st_storages(dao: DatabaseStudyDao) -> None:
    dao.save_area("area_1")

    dao.save_st_storages(
        "area_1",
        [
            STStorage(id="st_storage_id_1", name="st-storage-1", efficiency=0.8),
            STStorage(id="st_storage_id_2", name="st-storage-2", efficiency=0.9),
        ],
    )

    st_storage_1 = dao.get_st_storage("area_1", "st_storage_id_1")
    assert st_storage_1.id == "st_storage_id_1"
    assert st_storage_1.name == "st-storage-1"
    assert st_storage_1.efficiency == 0.8

    st_storage_2 = dao.get_st_storage("area_1", "st_storage_id_2")
    assert st_storage_2.id == "st_storage_id_2"
    assert st_storage_2.name == "st-storage-2"
    assert st_storage_2.efficiency == 0.9

    all_storages = dao.get_all_st_storages_for_area("area_1")
    assert len(all_storages) == 2

    with pytest.raises(STStorageNotFound):
        dao.save_st_storages(
            "nonexistent",
            [STStorage(id="s1", name="s1"), STStorage(id="s2", name="s2")],
        )


def test_get_all_st_storages(dao: DatabaseStudyDao) -> None:
    dao.save_area("area_1")
    dao.save_area("area_2")

    dao.save_st_storage("area_1", STStorage(id="st_storage_id_1", name="st-storage-1", efficiency=0.8))
    dao.save_st_storage("area_2", STStorage(id="st_storage_id_2", name="st-storage-2", efficiency=0.9))

    all_storages = dao.get_all_st_storages()
    assert len(all_storages) == 2
    assert all_storages["area_1"]["st_storage_id_1"].id == "st_storage_id_1"
    assert all_storages["area_2"]["st_storage_id_2"].id == "st_storage_id_2"


def test_get_st_storage_raises_when_missing(dao: DatabaseStudyDao) -> None:
    dao.save_area("area_1")
    dao.save_st_storage("area_1", STStorage(id="st_storage_id_1", name="st-storage-1"))

    with pytest.raises(STStorageNotFound):
        dao.get_st_storage("area_1", "nonexistent")

    with pytest.raises(STStorageNotFound):
        dao.get_st_storage("nonexistent", "st_storage_id_1")


def test_st_storage_exists(dao: DatabaseStudyDao) -> None:
    dao.save_area("area_1")
    dao.save_st_storage("area_1", STStorage(id="st_storage_id_1", name="st-storage-1", efficiency=0.8))
    assert dao.st_storage_exists("area_1", "st_storage_id_1")


def test_st_storage_exists_returns_false_for_unknown(dao: DatabaseStudyDao) -> None:
    assert not dao.st_storage_exists("nonexistent", "st_storage_id_1")


def test_delete_st_storage(dao: DatabaseStudyDao) -> None:
    dao.save_area("area_1")

    dao.save_st_storage("area_1", STStorage(id="st_storage_id_1", name="st-storage-1", efficiency=0.8))
    assert dao.st_storage_exists("area_1", "st_storage_id_1")

    with pytest.raises(STStorageNotFound):
        dao.delete_st_storage("area_1", STStorage(id="nonexistent", name="x"))
    with pytest.raises(STStorageNotFound):
        dao.delete_st_storage("nonexistent", STStorage(id="st_storage_id_1", name="x"))

    dao.delete_st_storage("area_1", STStorage(id="st_storage_id_1", name="st-storage-1"))
    assert not dao.st_storage_exists("area_1", "st_storage_id_1")

    with pytest.raises(STStorageNotFound):
        dao.get_st_storage("area_1", "st_storage_id_1")


def test_save_additional_constraints(dao: DatabaseStudyDao) -> None:
    dao.save_area("area_1")
    dao.save_st_storage("area_1", STStorage(id="st_storage_id_1", name="st-storage-1", efficiency=0.8))

    dao.save_st_storage_additional_constraints(
        "area_1",
        storage_id="st_storage_id_1",
        constraints=[
            STStorageAdditionalConstraint(id="constraint_id_1", name="constraint-1"),
            STStorageAdditionalConstraint(id="constraint_id_2", name="constraint-2"),
        ],
    )

    constraints = dao.get_all_st_storage_additional_constraints()
    assert len(constraints["area_1"]["st_storage_id_1"]) == 2
    assert constraints["area_1"]["st_storage_id_1"][0].id == "constraint_id_1"
    assert constraints["area_1"]["st_storage_id_1"][1].id == "constraint_id_2"

    with pytest.raises(STStorageNotFound):
        dao.save_st_storage_additional_constraints(
            "area_1",
            storage_id="nonexistent",
            constraints=[STStorageAdditionalConstraint(id="c1", name="c1")],
        )


def test_delete_additional_constraints(dao: DatabaseStudyDao) -> None:
    dao.save_area("area_1")
    dao.save_st_storage("area_1", STStorage(id="st_storage_id_1", name="st-storage-1", efficiency=0.8))

    dao.save_st_storage_additional_constraints(
        "area_1",
        storage_id="st_storage_id_1",
        constraints=[
            STStorageAdditionalConstraint(id="constraint_id_1", name="constraint-1"),
            STStorageAdditionalConstraint(id="constraint_id_2", name="constraint-2"),
            STStorageAdditionalConstraint(id="constraint_id_3", name="constraint-3"),
        ],
    )

    assert len(dao.get_all_st_storage_additional_constraints()["area_1"]["st_storage_id_1"]) == 3
    dao.delete_st_storage_additional_constraints("area_1", "st_storage_id_1", ["constraint_id_2", "constraint_id_3"])
    assert len(dao.get_all_st_storage_additional_constraints()["area_1"]["st_storage_id_1"]) == 1


def test_get_all_additional_constraints(dao: DatabaseStudyDao) -> None:
    dao.save_area("area_1")
    dao.save_st_storage("area_1", STStorage(id="st_storage_id_1", name="st-storage-1"))

    dao.save_st_storage_additional_constraints(
        "area_1",
        storage_id="st_storage_id_1",
        constraints=[
            STStorageAdditionalConstraint(id="constraint_id_1", name="constraint-1"),
            STStorageAdditionalConstraint(id="constraint_id_2", name="constraint-2"),
            STStorageAdditionalConstraint(id="constraint_id_3", name="constraint-3"),
        ],
    )

    assert len(dao.get_st_storage_additional_constraints("area_1", "st_storage_id_1")) == 3
    assert dao.get_st_storage_additional_constraints("area_1", "st_storage_id_2") == []


def test_st_storage_matrices_lifecycle(db_session: Session, dao: DatabaseStudyDao) -> None:
    dao.save_area("area_1")
    dao.save_st_storage("area_1", STStorage(id="battery", name="Battery"))

    matrix_service = dao._matrix_service
    dataframe = pl.DataFrame(data=[[1, 2.5], [3, 4.7]], orient="row")
    series_id = matrix_service.create(dataframe)

    dao.save_st_storage_pmax_injection("area_1", "battery", series_id)
    dao.save_st_storage_pmax_withdrawal("area_1", "battery", series_id)
    dao.save_st_storage_lower_rule_curve("area_1", "battery", series_id)
    dao.save_st_storage_upper_rule_curve("area_1", "battery", series_id)
    dao.save_st_storage_inflows("area_1", "battery", series_id)
    dao.save_st_storage_cost_injection("area_1", "battery", series_id)
    dao.save_st_storage_cost_withdrawal("area_1", "battery", series_id)
    dao.save_st_storage_cost_level("area_1", "battery", series_id)
    dao.save_st_storage_cost_variation_injection("area_1", "battery", series_id)
    dao.save_st_storage_cost_variation_withdrawal("area_1", "battery", series_id)

    pl.testing.assert_frame_equal(dao.get_st_storage_pmax_injection("area_1", "battery"), dataframe, check_dtypes=False)
    pl.testing.assert_frame_equal(
        dao.get_st_storage_pmax_withdrawal("area_1", "battery"), dataframe, check_dtypes=False
    )
    pl.testing.assert_frame_equal(
        dao.get_st_storage_lower_rule_curve("area_1", "battery"), dataframe, check_dtypes=False
    )
    pl.testing.assert_frame_equal(
        dao.get_st_storage_upper_rule_curve("area_1", "battery"), dataframe, check_dtypes=False
    )
    pl.testing.assert_frame_equal(dao.get_st_storage_inflows("area_1", "battery"), dataframe, check_dtypes=False)
    pl.testing.assert_frame_equal(
        dao.get_st_storage_cost_injection("area_1", "battery"), dataframe, check_dtypes=False
    )
    pl.testing.assert_frame_equal(
        dao.get_st_storage_cost_withdrawal("area_1", "battery"), dataframe, check_dtypes=False
    )
    pl.testing.assert_frame_equal(dao.get_st_storage_cost_level("area_1", "battery"), dataframe, check_dtypes=False)
    pl.testing.assert_frame_equal(
        dao.get_st_storage_cost_variation_injection("area_1", "battery"), dataframe, check_dtypes=False
    )
    pl.testing.assert_frame_equal(
        dao.get_st_storage_cost_variation_withdrawal("area_1", "battery"), dataframe, check_dtypes=False
    )

    # Cascade delete: deleting the storage should remove all matrix rows
    dao.delete_st_storage("area_1", STStorage(id="battery", name="Battery"))

    with db_session:
        assert db_session.execute(select(ST_STORAGE_TABLE)).fetchall() == []
        assert db_session.execute(select(PMAX_INJECTION_TABLE)).fetchall() == []
        assert db_session.execute(select(PMAX_WITHDRAWAL_TABLE)).fetchall() == []
        assert db_session.execute(select(LOWER_RULE_CURVE_TABLE)).fetchall() == []
        assert db_session.execute(select(UPPER_RULE_CURVE_TABLE)).fetchall() == []
        assert db_session.execute(select(INFLOWS_TABLE)).fetchall() == []
        assert db_session.execute(select(COST_INJECTION_TABLE)).fetchall() == []
        assert db_session.execute(select(COST_WITHDRAWAL_TABLE)).fetchall() == []
        assert db_session.execute(select(COST_LEVEL_TABLE)).fetchall() == []
        assert db_session.execute(select(COST_VARIATION_INJECTION_TABLE)).fetchall() == []
        assert db_session.execute(select(COST_VARIATION_WITHDRAWAL_TABLE)).fetchall() == []


def test_get_st_storage_matrix_raises_when_missing(dao: DatabaseStudyDao) -> None:
    dao.save_area("area_1")
    dao.save_st_storage("area_1", STStorage(id="battery", name="Battery"))

    getters = [
        dao.get_st_storage_pmax_injection,
        dao.get_st_storage_pmax_withdrawal,
        dao.get_st_storage_lower_rule_curve,
        dao.get_st_storage_upper_rule_curve,
        dao.get_st_storage_inflows,
        dao.get_st_storage_cost_injection,
        dao.get_st_storage_cost_withdrawal,
        dao.get_st_storage_cost_level,
        dao.get_st_storage_cost_variation_injection,
        dao.get_st_storage_cost_variation_withdrawal,
    ]
    for getter in getters:
        with pytest.raises(STStorageNotFound):
            getter("area_1", "battery")
        with pytest.raises(STStorageNotFound):
            getter("nonexistent", "battery")


def test_save_st_storage_matrix_raises_when_missing(dao: DatabaseStudyDao) -> None:
    dao.save_area("area_1")

    savers = [
        dao.save_st_storage_pmax_injection,
        dao.save_st_storage_pmax_withdrawal,
        dao.save_st_storage_lower_rule_curve,
        dao.save_st_storage_upper_rule_curve,
        dao.save_st_storage_inflows,
        dao.save_st_storage_cost_injection,
        dao.save_st_storage_cost_withdrawal,
        dao.save_st_storage_cost_level,
        dao.save_st_storage_cost_variation_injection,
        dao.save_st_storage_cost_variation_withdrawal,
    ]
    for saver in savers:
        with pytest.raises(STStorageNotFound):
            saver("area_1", "battery", "missing-matrix-id")
        with pytest.raises(STStorageNotFound):
            saver("nonexistent", "battery", "missing-matrix-id")


def test_constraint_matrix_lifecycle(db_session: Session, dao: DatabaseStudyDao) -> None:
    dao.save_area("area_1")
    dao.save_st_storage("area_1", STStorage(id="battery", name="Battery"))
    dao.save_st_storage_additional_constraints(
        "area_1",
        storage_id="battery",
        constraints=[STStorageAdditionalConstraint(id="c1", name="constraint-1")],
    )

    matrix_service = dao._matrix_service
    dataframe = pl.DataFrame(data=[[1, 2.5], [3, 4.7]], orient="row")
    series_id = matrix_service.create(dataframe)

    dao.save_st_storage_constraint_matrix("area_1", "battery", "c1", series_id)
    pl.testing.assert_frame_equal(
        dao.get_st_storage_additional_constraints_matrix("area_1", "battery", "c1"), dataframe, check_dtypes=False
    )

    with pytest.raises(STStorageNotFound):
        dao.get_st_storage_additional_constraints_matrix("area_1", "battery", "nonexistent")

    with pytest.raises(STStorageAdditionalConstraintNotFound):
        dao.save_st_storage_constraint_matrix("area_1", "battery", "nonexistent", series_id)

    # Cascade delete: deleting the storage removes constraints and their matrices
    dao.delete_st_storage("area_1", STStorage(id="battery", name="Battery"))

    with db_session:
        assert db_session.execute(select(ST_STORAGE_ADDITIONAL_CONSTRAINT_TABLE)).fetchall() == []
        assert db_session.execute(select(ST_STORAGE_ADDITIONAL_CONSTRAINT_MATRIX_TABLE)).fetchall() == []


def test_area_with_no_storages_absent_from_dict(dao: DatabaseStudyDao) -> None:
    dao.save_area("area_1")
    dao.save_area("area_2")

    dao.save_st_storage("area_1", STStorage(id="battery", name="Battery"))

    all_storages = dao.get_all_st_storages()
    assert "area_2" not in all_storages
    assert "area_1" in all_storages
    assert "battery" in all_storages["area_1"]
