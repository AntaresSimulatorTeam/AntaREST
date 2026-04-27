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

from unittest.mock import Mock

import pytest

from antarest.blobstore.in_memory import InMemoryBlobService
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.business.model.reserve_definition_model import ReserveDefinition, ReserveType
from antarest.study.business.model.reserves_global_parameters_model import ReservesGlobalParameters
from antarest.study.dao.file.file_study_dao import FileStudyTreeDao
from antarest.study.model import STUDY_VERSION_10_0
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from tests.study.dao.utils import save_area


@pytest.fixture
def filestudy_dao_v10(empty_study_930: FileStudy, matrix_service: ISimpleMatrixService) -> FileStudyTreeDao:
    empty_study_930.config.version = STUDY_VERSION_10_0
    constants = GeneratorMatrixConstants(matrix_service)
    constants.init_constant_matrices()
    return FileStudyTreeDao(
        empty_study_930,
        False,
        constants,
        InMemoryBlobService(),
        matrix_service,
        Mock(),
    )


def _make_reserve(id_: str, reserve_type: ReserveType = ReserveType.UP, **overrides) -> ReserveDefinition:
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


class TestCoexistenceWithGlobalParameters:
    """Reserves and global parameters share the same INI file per area — ensure they don't overwrite each other."""

    def test_get_all_excludes_global_parameters_section(self, filestudy_dao_v10: FileStudyTreeDao) -> None:
        save_area(filestudy_dao_v10, "paris")
        filestudy_dao_v10.save_reserves_global_parameters(
            {"paris": ReservesGlobalParameters(reference_activation_duration_up=7)}
        )
        filestudy_dao_v10.save_reserve_definitions(
            {"paris": [_make_reserve("Reserve 1"), _make_reserve("Reserve 2", ReserveType.DOWN)]}
        )

        reserves = list(filestudy_dao_v10.get_all_reserve_definitions_for_area("paris"))
        ids = sorted(r.id for r in reserves)
        assert ids == ["Reserve 1", "Reserve 2"]
        assert "globalparameters" not in ids

    def test_save_reserve_preserves_global_parameters(self, filestudy_dao_v10: FileStudyTreeDao) -> None:
        save_area(filestudy_dao_v10, "paris")
        global_params = ReservesGlobalParameters(
            reference_activation_duration_up=42,
            energy_activation_ratio_down=0.33,
        )
        filestudy_dao_v10.save_reserves_global_parameters({"paris": global_params})
        filestudy_dao_v10.save_reserve_definitions({"paris": [_make_reserve("R1")]})

        assert filestudy_dao_v10.get_reserves_global_parameters("paris") == global_params

    def test_save_global_parameters_preserves_reserves(self, filestudy_dao_v10: FileStudyTreeDao) -> None:
        save_area(filestudy_dao_v10, "paris")
        reserve = _make_reserve("R1")
        filestudy_dao_v10.save_reserve_definitions({"paris": [reserve]})
        filestudy_dao_v10.save_reserves_global_parameters(
            {"paris": ReservesGlobalParameters(reference_activation_duration_up=9)}
        )

        assert filestudy_dao_v10.get_reserve_definition("paris", "R1") == reserve

    def test_delete_reserve_preserves_global_parameters(self, filestudy_dao_v10: FileStudyTreeDao) -> None:
        save_area(filestudy_dao_v10, "paris")
        global_params = ReservesGlobalParameters(reference_activation_duration_up=11)
        filestudy_dao_v10.save_reserves_global_parameters({"paris": global_params})
        filestudy_dao_v10.save_reserve_definitions({"paris": [_make_reserve("R1")]})

        filestudy_dao_v10.delete_reserve_definitions("paris", ["R1"])

        assert filestudy_dao_v10.get_reserves_global_parameters("paris") == global_params
        assert filestudy_dao_v10.reserve_definition_exists("paris", "R1") is False

    def test_upsert_multiple_reserves_preserves_global_parameters(self, filestudy_dao_v10: FileStudyTreeDao) -> None:
        save_area(filestudy_dao_v10, "paris")
        global_params = ReservesGlobalParameters(reference_activation_duration_down=5)
        filestudy_dao_v10.save_reserves_global_parameters({"paris": global_params})
        filestudy_dao_v10.save_reserve_definitions(
            {"paris": [_make_reserve("R1"), _make_reserve("R2", ReserveType.DOWN)]}
        )
        filestudy_dao_v10.save_reserve_definitions(
            {"paris": [_make_reserve("R1", failure_cost=999.0), _make_reserve("R3")]}
        )

        assert filestudy_dao_v10.get_reserves_global_parameters("paris") == global_params
        assert filestudy_dao_v10.get_reserve_definition("paris", "R1").failure_cost == 999.0
        assert filestudy_dao_v10.reserve_definition_exists("paris", "R2") is True
        assert filestudy_dao_v10.reserve_definition_exists("paris", "R3") is True
