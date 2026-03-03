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

from antarest.core.exceptions import AreaNotFound, STStorageAdditionalConstraintNotFound, STStorageNotFound
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


def test_save_st_storage(db_dao_930: DatabaseStudyDao) -> None:
    dao = db_dao_930
    dao.save_area("area_1")

    dao.save_st_storage(
        "area_1",
        STStorage(
            id="st_storage_id",
            name="st-storage",
            group="battery",
            injection_nominal_capacity=100.0,
            withdrawal_nominal_capacity=200.0,
            reservoir_capacity=500.0,
            efficiency=0.8,
            initial_level=0.3,
            initial_level_optim=True,
            enabled=True,
            efficiency_withdrawal=0.9,
            penalize_variation_injection=True,
            penalize_variation_withdrawal=False,
            allow_overflow=True,
        ),
    )

    st_storage = dao.get_st_storage("area_1", "st_storage_id")
    assert st_storage.id == "st_storage_id"
    assert st_storage.name == "st-storage"
    assert st_storage.group == "battery"
    assert st_storage.injection_nominal_capacity == 100.0
    assert st_storage.withdrawal_nominal_capacity == 200.0
    assert st_storage.reservoir_capacity == 500.0
    assert st_storage.efficiency == 0.8
    assert st_storage.initial_level == 0.3
    assert st_storage.initial_level_optim is True
    assert st_storage.enabled is True
    assert st_storage.efficiency_withdrawal == 0.9
    assert st_storage.penalize_variation_injection is True
    assert st_storage.penalize_variation_withdrawal is False
    assert st_storage.allow_overflow is True

    with pytest.raises(AreaNotFound):
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

    with pytest.raises(AreaNotFound):
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

    with pytest.raises(AreaNotFound):
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
    with pytest.raises(AreaNotFound):
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
    pmax_injection_df = pl.DataFrame(data=[[1, 2.5], [3, 4.7]], orient="row")
    pmax_withdrawal_df = pl.DataFrame(data=[[5, 6.1], [7, 8.3]], orient="row")
    lower_rule_curve_df = pl.DataFrame(data=[[9, 10.2], [11, 12.4]], orient="row")
    upper_rule_curve_df = pl.DataFrame(data=[[13, 14.6], [15, 16.8]], orient="row")
    inflows_df = pl.DataFrame(data=[[17, 18.9], [19, 20.1]], orient="row")
    cost_injection_df = pl.DataFrame(data=[[21, 22.2], [23, 24.4]], orient="row")
    cost_withdrawal_df = pl.DataFrame(data=[[25, 26.5], [27, 28.7]], orient="row")
    cost_level_df = pl.DataFrame(data=[[29, 30.8], [31, 32.0]], orient="row")
    cost_variation_injection_df = pl.DataFrame(data=[[33, 34.1], [35, 36.3]], orient="row")
    cost_variation_withdrawal_df = pl.DataFrame(data=[[37, 38.4], [39, 40.6]], orient="row")

    dao.save_st_storage_pmax_injection("area_1", "battery", matrix_service.create(pmax_injection_df))
    dao.save_st_storage_pmax_withdrawal("area_1", "battery", matrix_service.create(pmax_withdrawal_df))
    dao.save_st_storage_lower_rule_curve("area_1", "battery", matrix_service.create(lower_rule_curve_df))
    dao.save_st_storage_upper_rule_curve("area_1", "battery", matrix_service.create(upper_rule_curve_df))
    dao.save_st_storage_inflows("area_1", "battery", matrix_service.create(inflows_df))
    dao.save_st_storage_cost_injection("area_1", "battery", matrix_service.create(cost_injection_df))
    dao.save_st_storage_cost_withdrawal("area_1", "battery", matrix_service.create(cost_withdrawal_df))
    dao.save_st_storage_cost_level("area_1", "battery", matrix_service.create(cost_level_df))
    dao.save_st_storage_cost_variation_injection(
        "area_1", "battery", matrix_service.create(cost_variation_injection_df)
    )
    dao.save_st_storage_cost_variation_withdrawal(
        "area_1", "battery", matrix_service.create(cost_variation_withdrawal_df)
    )

    pl.testing.assert_frame_equal(
        dao.get_st_storage_pmax_injection("area_1", "battery"), pmax_injection_df, check_dtypes=False
    )
    pl.testing.assert_frame_equal(
        dao.get_st_storage_pmax_withdrawal("area_1", "battery"), pmax_withdrawal_df, check_dtypes=False
    )
    pl.testing.assert_frame_equal(
        dao.get_st_storage_lower_rule_curve("area_1", "battery"), lower_rule_curve_df, check_dtypes=False
    )
    pl.testing.assert_frame_equal(
        dao.get_st_storage_upper_rule_curve("area_1", "battery"), upper_rule_curve_df, check_dtypes=False
    )
    pl.testing.assert_frame_equal(dao.get_st_storage_inflows("area_1", "battery"), inflows_df, check_dtypes=False)
    pl.testing.assert_frame_equal(
        dao.get_st_storage_cost_injection("area_1", "battery"), cost_injection_df, check_dtypes=False
    )
    pl.testing.assert_frame_equal(
        dao.get_st_storage_cost_withdrawal("area_1", "battery"), cost_withdrawal_df, check_dtypes=False
    )
    pl.testing.assert_frame_equal(dao.get_st_storage_cost_level("area_1", "battery"), cost_level_df, check_dtypes=False)
    pl.testing.assert_frame_equal(
        dao.get_st_storage_cost_variation_injection("area_1", "battery"),
        cost_variation_injection_df,
        check_dtypes=False,
    )
    pl.testing.assert_frame_equal(
        dao.get_st_storage_cost_variation_withdrawal("area_1", "battery"),
        cost_variation_withdrawal_df,
        check_dtypes=False,
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
        with pytest.raises(AreaNotFound):
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
        with pytest.raises(AreaNotFound):
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
        dao.get_st_storage_additional_constraint_matrix("area_1", "battery", "c1"), dataframe, check_dtypes=False
    )

    with pytest.raises(STStorageAdditionalConstraintNotFound):
        dao.get_st_storage_additional_constraint_matrix("area_1", "battery", "nonexistent")

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
