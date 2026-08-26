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
import re
from typing import Any
from unittest.mock import Mock

import pytest

from antarest.blobstore.in_memory import InMemoryBlobService
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.business.model.reserve_certification_model import StorageReserveCertification
from antarest.study.business.model.reserve_definition_model import ReserveDefinition, ReserveType
from antarest.study.dao.file.file_study_dao import FileStudyTreeDao
from antarest.study.model import STUDY_VERSION_10_2
from antarest.study.storage.rawstudy.model.filesystem.config.reserve_participations import (
    parse_hydro_reserves_certifications,
    parse_hydro_reserves_symmetries,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.yaml_file_node import YAMLReader
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from tests.study.dao.utils import save_area


@pytest.fixture
def filestudy_dao_v10_2(empty_study_930: FileStudy, matrix_service: ISimpleMatrixService) -> FileStudyTreeDao:
    empty_study_930.config.version = STUDY_VERSION_10_2
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


def _hydro_reserve_file(dao: FileStudyTreeDao, area_id: str):
    return (
        dao.get_file_study().config.study_path
        / "input"
        / "hydro"
        / "common"
        / "reserves"
        / area_id
        / "reserve-participations.yml"
    )


def _set_up(dao: FileStudyTreeDao) -> None:
    save_area(dao, "paris")
    dao.save_reserve_definitions(
        {"paris": [ReserveDefinition(name=name, type=ReserveType.UP) for name in ["r1", "r2"]]}
    )


def test_parsing_errors() -> None:
    # Duplicated reserve
    content = {"participations": {"certifications": [{"reserve": "r1"}, {"reserve": "r1"}]}}
    with pytest.raises(ValueError, match="Some reserves are duplicated for the long-term storage"):
        parse_hydro_reserves_certifications(content)

    # One symmetry only
    content = {"participations": {"symmetries": [{"reserves": ["r1"]}]}}
    with pytest.raises(
        ValueError, match=re.escape("Reserve symmetries should have at least 2 elements, and was ['r1']")
    ):
        parse_hydro_reserves_symmetries(content)

    # Duplicated reserve in symmetry
    content = {"participations": {"symmetries": [{"reserves": ["r1", "r1"]}]}}
    with pytest.raises(ValueError, match="Reserve symmetries should not contain duplicates"):
        parse_hydro_reserves_symmetries(content)

    # Negative values are refused
    content = {"participations": {"certifications": [{"reserve": "r1", "max-release": -1.0}]}}
    with pytest.raises(ValueError):
        parse_hydro_reserves_certifications(content)

    # Unlike thermal and short-term storage, there is no asset id to give
    content = {"participations": {"cluster": "th1", "certifications": []}}
    with pytest.raises(ValueError):
        parse_hydro_reserves_certifications(content)


def test_yaml_file_is_written_and_read_correctly(filestudy_dao_v10_2: FileStudyTreeDao) -> None:
    dao = filestudy_dao_v10_2
    _set_up(dao)

    dao.save_hydro_reserve_certifications(
        {"paris": {"r1": StorageReserveCertification(participation_cost=1.0, max_release=2.0, max_store=3.0)}}
    )

    content = YAMLReader().read(_hydro_reserve_file(dao, "paris"))
    expected_content: dict[str, Any] = {
        "participations": {
            "certifications": [
                {"reserve": "r1", "participation-cost": 1.0, "max-release": 2.0, "max-store": 3.0},
            ]
        }
    }
    assert content == expected_content

    assert dao.get_hydro_reserve_certifications("paris") == {
        "r1": StorageReserveCertification(participation_cost=1.0, max_release=2.0, max_store=3.0)
    }


def test_reading_an_area_without_the_file_returns_nothing(filestudy_dao_v10_2: FileStudyTreeDao) -> None:
    dao = filestudy_dao_v10_2
    _set_up(dao)

    assert not _hydro_reserve_file(dao, "paris").exists()
    assert dao.get_hydro_reserve_certifications("paris") == {}


def _save_existing_content_with_a_symmetry(dao: FileStudyTreeDao) -> None:
    existing_content = {
        "participations": {
            "certifications": [{"reserve": "r1", "max-release": 9.0}],
            "symmetries": [{"reserves": ["r1", "r2"]}],
        }
    }
    dao.get_file_study().tree.save(
        existing_content, ["input", "hydro", "common", "reserves", "paris", "reserve-participations"]
    )


def test_saving_certifications_preserves_the_symmetries(filestudy_dao_v10_2: FileStudyTreeDao) -> None:
    # Symmetries are not handled by the DAO yet, but they share the file with the certifications,
    # so saving certifications must not drop the ones that are still certified.
    dao = filestudy_dao_v10_2
    _set_up(dao)
    _save_existing_content_with_a_symmetry(dao)

    dao.save_hydro_reserve_certifications(
        {
            "paris": {
                "r1": StorageReserveCertification(max_release=9.0),
                "r2": StorageReserveCertification(max_store=4.0),
            }
        }
    )

    content = YAMLReader().read(_hydro_reserve_file(dao, "paris"))
    assert content == {
        "participations": {
            "certifications": [
                {"reserve": "r1", "participation-cost": 0.0, "max-release": 9.0, "max-store": 0.0},
                {"reserve": "r2", "participation-cost": 0.0, "max-release": 0.0, "max-store": 4.0},
            ],
            "symmetries": [{"reserves": ["r1", "r2"]}],
        }
    }


def test_saving_certifications_removes_the_orphan_symmetries(filestudy_dao_v10_2: FileStudyTreeDao) -> None:
    # A symmetry whose reserves lost their certification must be dropped: it would be left with a
    # single reserve, which `_symmetry_validator` rejects on the next read.
    dao = filestudy_dao_v10_2
    _set_up(dao)
    _save_existing_content_with_a_symmetry(dao)

    # "r1" loses its certification, so the ["r1", "r2"] symmetry is left with a single reserve.
    dao.save_hydro_reserve_certifications({"paris": {"r2": StorageReserveCertification(max_store=4.0)}})

    content = YAMLReader().read(_hydro_reserve_file(dao, "paris"))
    assert content == {
        "participations": {
            "certifications": [
                {"reserve": "r2", "participation-cost": 0.0, "max-release": 0.0, "max-store": 4.0},
            ],
        }
    }


def test_saving_empty_certifications_removes_the_symmetries(filestudy_dao_v10_2: FileStudyTreeDao) -> None:
    dao = filestudy_dao_v10_2
    _set_up(dao)
    _save_existing_content_with_a_symmetry(dao)

    dao.save_hydro_reserve_certifications({"paris": {}})

    content = YAMLReader().read(_hydro_reserve_file(dao, "paris"))
    assert content == {"participations": {}}
