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

from antarest.core.exceptions import AreaNotFound, ReserveDefinitionNotFound, ReserveDefinitionsNotFound
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.business.model.area_properties_model import AreaProperties
from antarest.study.business.model.reserve_definition_model import (
    ReserveDefinition,
    ReserveDefinitionId,
    ReserveType,
)
from antarest.study.business.model.reserves_global_parameters_model import ReservesGlobalParameters
from antarest.study.business.model.thermal_cluster_model import ThermalCluster, initialize_thermal_cluster
from antarest.study.business.model.thermal_reserve_certification_model import ThermalReserveCertification
from antarest.study.dao.api.study_dao import StudyDao
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

    fetched = dao_10_0.get_reserve_definition("paris", "r1")
    assert fetched.failure_cost == 999.0


def test_save_raises_area_not_found_when_area_missing(dao_10_0: StudyDao) -> None:
    with pytest.raises(AreaNotFound):
        dao_10_0.save_reserve_definitions({"nonexistent": [_reserve("R1")]})


def test_reserve_definition_exists(dao_10_0: StudyDao) -> None:
    save_area(dao_10_0, "paris")
    dao_10_0.save_reserve_definitions({"paris": [_reserve("R1")]})

    assert dao_10_0.reserve_definition_exists("paris", "r1") is True
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
    assert {r.id for r in fetched} == {"r1", "r2"}


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
    assert set(result["paris"].keys()) == {"r1", "r2"}
    assert set(result["lyon"].keys()) == {"r1"}


def test_delete(dao_10_0: StudyDao) -> None:
    save_area(dao_10_0, "paris")
    dao_10_0.save_reserve_definitions({"paris": [_reserve("R1"), _reserve("R2")]})

    dao_10_0.delete_reserve_definitions("paris", ["r1"])

    assert dao_10_0.reserve_definition_exists("paris", "r1") is False
    assert dao_10_0.reserve_definition_exists("paris", "r2") is True


def test_delete_not_found_raises(dao_10_0: StudyDao) -> None:
    save_area(dao_10_0, "paris")
    with pytest.raises((ReserveDefinitionNotFound, ReserveDefinitionsNotFound)):
        dao_10_0.delete_reserve_definitions("paris", ["unknown"])


def test_save_and_retrieve_reserve_need(dao_10_0: StudyDao, matrix_service: ISimpleMatrixService) -> None:
    save_area(dao_10_0, "paris")
    dao_10_0.save_reserve_definitions({"paris": [_reserve("R1")]})

    matrix_df = pl.DataFrame([[0.0]] * 8760, orient="row")
    matrix_id = matrix_service.create(matrix_df)
    dao_10_0.save_reserve_needs({"paris": {ReserveDefinitionId("r1"): matrix_id}})

    fetched = dao_10_0.get_reserve_need("paris", "r1")
    assert fetched.shape == (8760, 1)


def test_get_all_reserve_needs_empty(dao_10_0: StudyDao) -> None:
    save_area(dao_10_0, "paris")
    assert dao_10_0.get_all_reserve_needs() == {}


def test_cascade_delete_on_area_removal(dao_10_0: StudyDao) -> None:
    save_area(dao_10_0, "paris")
    dao_10_0.save_reserve_definitions({"paris": [_reserve("R1")]})

    dao_10_0.delete_area("paris")

    assert dao_10_0.get_all_reserve_definitions() == {}


def test_removing_a_reserve_cascades_on_symmetries_and_certifications(dao_10_0: StudyDao) -> None:
    # Create 1 area with 2 thermal clusters and 4 reserves
    dao = dao_10_0
    dao.save_areas_with_properties({"fr": AreaProperties()})
    th1 = ThermalCluster(name="th1")
    th2 = ThermalCluster(name="th2")
    initialize_thermal_cluster(th1, dao.get_version())
    initialize_thermal_cluster(th2, dao.get_version())
    dao.save_thermals({"fr": [th1, th2]})
    reserves = []
    for reserve_name in ["r1", "r2", "r3", "r4"]:
        reserves.append(ReserveDefinition(name=reserve_name, type=ReserveType.DOWN))
    dao.save_reserve_definitions({"fr": reserves})

    # Save 1 symmetry and 1 certification.
    certification = ThermalReserveCertification()
    dao.save_thermal_reserve_certifications(
        {"fr": {"r1": {"th1": certification, "th2": certification}, "r2": {"th1": certification}}}
    )
    dao.save_thermal_reserve_symmetries({"fr": {"th1": [["r1", "r2"]]}})

    # Remove the reserve `r1`. We should no longer see `r1` in the symmetries and certifications.
    dao.delete_reserve_definitions("fr", ["r1"])

    assert dao.get_thermal_reserve_symmetries("fr") == {}
    assert dao.get_thermal_reserve_certifications("fr") == {"r2": {"th1": certification}}


class TestCoexistenceWithGlobalParameters:
    """On the filesystem, reserves and global parameters share the same file per area — ensure they don't
    overwrite each other. The same expectations must hold for the database backend."""

    def test_get_all_excludes_global_parameters_section(self, dao_10_0: StudyDao) -> None:
        save_area(dao_10_0, "paris")
        dao_10_0.save_reserves_global_parameters(
            {"paris": ReservesGlobalParameters(reference_activation_duration_up=7)}
        )
        dao_10_0.save_reserve_definitions({"paris": [_reserve("Reserve 1"), _reserve("Reserve 2", ReserveType.DOWN)]})

        reserves = list(dao_10_0.get_all_reserve_definitions_for_area("paris"))
        ids = sorted(r.id for r in reserves)
        assert ids == ["reserve 1", "reserve 2"]
        assert "globalparameters" not in ids

    def test_save_reserve_preserves_global_parameters(self, dao_10_0: StudyDao) -> None:
        save_area(dao_10_0, "paris")
        global_params = ReservesGlobalParameters(
            reference_activation_duration_up=42,
            energy_activation_ratio_down=0.33,
        )
        dao_10_0.save_reserves_global_parameters({"paris": global_params})
        dao_10_0.save_reserve_definitions({"paris": [_reserve("R1")]})

        assert dao_10_0.get_reserves_global_parameters("paris") == global_params

    def test_save_global_parameters_preserves_reserves(self, dao_10_0: StudyDao) -> None:
        save_area(dao_10_0, "paris")
        reserve = _reserve("R1")
        dao_10_0.save_reserve_definitions({"paris": [reserve]})
        dao_10_0.save_reserves_global_parameters(
            {"paris": ReservesGlobalParameters(reference_activation_duration_up=9)}
        )

        assert dao_10_0.get_reserve_definition("paris", "r1") == reserve

    def test_delete_reserve_preserves_global_parameters(self, dao_10_0: StudyDao) -> None:
        save_area(dao_10_0, "paris")
        global_params = ReservesGlobalParameters(reference_activation_duration_up=11)
        dao_10_0.save_reserves_global_parameters({"paris": global_params})
        dao_10_0.save_reserve_definitions({"paris": [_reserve("R1")]})

        dao_10_0.delete_reserve_definitions("paris", ["r1"])

        assert dao_10_0.get_reserves_global_parameters("paris") == global_params
        assert dao_10_0.reserve_definition_exists("paris", "r1") is False

    def test_upsert_multiple_reserves_preserves_global_parameters(self, dao_10_0: StudyDao) -> None:
        save_area(dao_10_0, "paris")
        global_params = ReservesGlobalParameters(reference_activation_duration_down=5)
        dao_10_0.save_reserves_global_parameters({"paris": global_params})
        dao_10_0.save_reserve_definitions({"paris": [_reserve("R1"), _reserve("R2", ReserveType.DOWN)]})
        dao_10_0.save_reserve_definitions({"paris": [_reserve("R1", failure_cost=999.0), _reserve("R3")]})

        assert dao_10_0.get_reserves_global_parameters("paris") == global_params
        assert dao_10_0.get_reserve_definition("paris", "r1").failure_cost == 999.0
        assert dao_10_0.reserve_definition_exists("paris", "r2") is True
        assert dao_10_0.reserve_definition_exists("paris", "r3") is True
