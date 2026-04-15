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
Tests for FileStudyReserveDefinitionDao.

Critical test focus: the reserves.ini file contains both [globalparameters]
(handled by the PR #3154) and [Reserve X] sections (handled by this PR).
Per-reserve CRUD operations must NOT clobber the [globalparameters] section,
and list/delete operations must NOT return or touch it.
"""

from pathlib import Path
from unittest.mock import Mock

import pytest
from antares.study.version.create_app import CreateApp

from antarest.blobstore.in_memory import InMemoryBlobService
from antarest.core.exceptions import AreaNotFound, ReserveDefinitionNotFound
from antarest.core.serde.ini_reader import IniReader
from antarest.core.serde.ini_writer import IniWriter
from antarest.matrixstore.matrix_uri_mapper import MatrixUriMapperFactory, NormalizedMatrixUriMapper
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.business.model.reserve_definition_model import ReserveDefinition, ReserveType
from antarest.study.business.model.reserves_global_parameters_model import ReservesGlobalParameters
from antarest.study.dao.file.file_study_dao import FileStudyTreeDao
from antarest.study.model import STUDY_VERSION_9_3
from antarest.study.storage.rawstudy.model.filesystem.config.files import build
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import FileStudyTree
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from tests.study.dao.utils import save_area


def _build_file_study_v10(tmp_path: Path, matrix_service: ISimpleMatrixService) -> FileStudy:
    """
    Build a v10.0 FileStudy by bootstrapping a v9.3 template (the antares-study-version
    package does not ship a v10.0 template yet) and then bumping the version in
    `study.antares` so `build()` reads it back as 10.0.
    """
    study_id = "5c22caca-b100-47e7-bbea-8b1b97aa26d9"
    study_path = tmp_path / study_id
    CreateApp(study_dir=study_path, caption="filestudy", version=STUDY_VERSION_9_3, author="Joe")()

    # Bump the version in study.antares before config build.
    antares_ini = study_path / "study.antares"
    content = IniReader().read(antares_ini)
    content["antares"]["version"] = "10.0"
    IniWriter().write(content, antares_ini)

    config = build(study_path, study_id)
    mapper_factory = MatrixUriMapperFactory(matrix_service=matrix_service)
    matrix_mapper = mapper_factory.create(NormalizedMatrixUriMapper.NORMALIZED)
    return FileStudy(config, FileStudyTree(matrix_mapper, config))


@pytest.fixture
def filestudy_dao_v10(tmp_path: Path, matrix_service: ISimpleMatrixService) -> FileStudyTreeDao:
    file_study = _build_file_study_v10(tmp_path, matrix_service)
    constants = GeneratorMatrixConstants(matrix_service)
    constants.init_constant_matrices()
    return FileStudyTreeDao(
        file_study,
        False,
        constants,
        InMemoryBlobService(),
        matrix_service,
        Mock(),
    )


def _make_reserve(name: str, reserve_type: ReserveType = ReserveType.UP, **overrides) -> ReserveDefinition:
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


class TestSaveAndGet:
    def test_save_then_get_round_trip(self, filestudy_dao_v10: FileStudyTreeDao) -> None:
        save_area(filestudy_dao_v10, "paris")
        reserve = _make_reserve("Reserve 1")
        filestudy_dao_v10.save_reserve_definitions({"paris": [reserve]})

        fetched = filestudy_dao_v10.get_reserve_definition("paris", reserve.id)
        assert fetched == reserve

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

    def test_reserve_definition_exists(self, filestudy_dao_v10: FileStudyTreeDao) -> None:
        save_area(filestudy_dao_v10, "paris")
        filestudy_dao_v10.save_reserve_definitions({"paris": [_make_reserve("Reserve 1")]})

        assert filestudy_dao_v10.reserve_definition_exists("paris", "Reserve 1") is True
        assert filestudy_dao_v10.reserve_definition_exists("paris", "Unknown") is False

    def test_get_raises_not_found(self, filestudy_dao_v10: FileStudyTreeDao) -> None:
        save_area(filestudy_dao_v10, "paris")
        with pytest.raises(ReserveDefinitionNotFound):
            filestudy_dao_v10.get_reserve_definition("paris", "unknown")

    def test_get_all_empty_area(self, filestudy_dao_v10: FileStudyTreeDao) -> None:
        save_area(filestudy_dao_v10, "paris")
        assert list(filestudy_dao_v10.get_all_reserve_definitions_for_area("paris")) == []

    def test_get_all_raises_area_not_found(self, filestudy_dao_v10: FileStudyTreeDao) -> None:
        with pytest.raises(AreaNotFound):
            list(filestudy_dao_v10.get_all_reserve_definitions_for_area("nonexistent"))

    def test_get_raises_area_not_found(self, filestudy_dao_v10: FileStudyTreeDao) -> None:
        with pytest.raises(AreaNotFound):
            filestudy_dao_v10.get_reserve_definition("nonexistent", "R1")

    def test_reserve_definition_exists_on_missing_area(self, filestudy_dao_v10: FileStudyTreeDao) -> None:
        assert filestudy_dao_v10.reserve_definition_exists("nonexistent", "R1") is False


class TestCoexistenceWithGlobalParameters:
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

        filestudy_dao_v10.delete_reserve_definition("paris", "R1")

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


class TestDelete:
    def test_delete_not_found_raises(self, filestudy_dao_v10: FileStudyTreeDao) -> None:
        save_area(filestudy_dao_v10, "paris")
        with pytest.raises(ReserveDefinitionNotFound):
            filestudy_dao_v10.delete_reserve_definition("paris", "unknown")

    def test_delete_leaves_other_reserves(self, filestudy_dao_v10: FileStudyTreeDao) -> None:
        save_area(filestudy_dao_v10, "paris")
        filestudy_dao_v10.save_reserve_definitions(
            {"paris": [_make_reserve("R1"), _make_reserve("R2", ReserveType.DOWN)]}
        )
        filestudy_dao_v10.delete_reserve_definition("paris", "R1")
        assert filestudy_dao_v10.reserve_definition_exists("paris", "R1") is False
        assert filestudy_dao_v10.reserve_definition_exists("paris", "R2") is True


class TestGetAll:
    def test_get_all_across_multiple_areas(self, filestudy_dao_v10: FileStudyTreeDao) -> None:
        save_area(filestudy_dao_v10, "paris")
        save_area(filestudy_dao_v10, "lyon")
        filestudy_dao_v10.save_reserve_definitions(
            {
                "paris": [_make_reserve("R1")],
                "lyon": [_make_reserve("R1"), _make_reserve("R2", ReserveType.DOWN)],
            }
        )

        result = filestudy_dao_v10.get_all_reserve_definitions()
        assert set(result.keys()) == {"paris", "lyon"}
        assert set(result["paris"].keys()) == {"R1"}
        assert set(result["lyon"].keys()) == {"R1", "R2"}
