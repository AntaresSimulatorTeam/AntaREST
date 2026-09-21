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

from pathlib import Path

import pytest

from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.business.model.gems.library import GemsLibrary
from antarest.study.business.model.gems.scenario_builder import GemsScBuilderMapping, GemsScenarioBuilder
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.dao.file.file_study_dao import FileStudyTreeDao
from antarest.study.dao.study_conversion.study_converter import StudyConverter
from antarest.study.model import STUDY_VERSION_10_2

ASSET = Path(__file__).parent.parent / "assets/gems/scenario_builder/modeler-scenariobuilder.dat"


def test_roundtrip(dao_10_2: StudyDao) -> None:
    assert dao_10_2.get_gems_scenario_builder() is None
    builder = GemsScenarioBuilder(
        scenarios={
            "load": [
                GemsScBuilderMapping(scenario=0, time_series_index=1),
                GemsScBuilderMapping(scenario=1, time_series_index=5),
            ],
            "hydro": [GemsScBuilderMapping(scenario=2, time_series_index=7)],
        }
    )
    dao_10_2.save_gems_scenario_builder(builder)
    assert dao_10_2.get_gems_scenario_builder() == builder
    dao_10_2.save_gems_scenario_builder(builder)
    assert dao_10_2.get_gems_scenario_builder() == builder


def test_replace_builder(dao_10_2: StudyDao) -> None:
    dao_10_2.save_gems_scenario_builder(
        GemsScenarioBuilder(
            scenarios={
                "load": [
                    GemsScBuilderMapping(scenario=0, time_series_index=1),
                    GemsScBuilderMapping(scenario=1, time_series_index=5),
                ],
                "hydro": [GemsScBuilderMapping(scenario=2, time_series_index=7)],
            }
        )
    )
    replacement = GemsScenarioBuilder(
        scenarios={
            "load": [GemsScBuilderMapping(scenario=0, time_series_index=4)],
            "wind": [GemsScBuilderMapping(scenario=1, time_series_index=2)],
        }
    )
    dao_10_2.save_gems_scenario_builder(replacement)
    assert dao_10_2.get_gems_scenario_builder() == replacement


def test_clear_builder(dao_10_2: StudyDao) -> None:
    builder = GemsScenarioBuilder(scenarios={"load": [GemsScBuilderMapping(scenario=0, time_series_index=1)]})
    dao_10_2.save_gems_scenario_builder(builder)
    dao_10_2.save_gems_scenario_builder(GemsScenarioBuilder())
    assert dao_10_2.get_gems_scenario_builder() is None
    dao_10_2.save_gems_scenario_builder(builder)
    assert dao_10_2.get_gems_scenario_builder() == builder


def test_empty_builder(dao_10_2: StudyDao) -> None:
    builder = GemsScenarioBuilder()
    dao_10_2.save_gems_scenario_builder(builder)
    assert dao_10_2.get_gems_scenario_builder() is None
    populated = GemsScenarioBuilder(scenarios={"load": [GemsScBuilderMapping(scenario=0, time_series_index=1)]})
    dao_10_2.save_gems_scenario_builder(populated)
    assert dao_10_2.get_gems_scenario_builder() == populated


def test_save_after_empty_file(filestudy_dao_v10_2: FileStudyTreeDao) -> None:
    dao = filestudy_dao_v10_2
    path = dao.get_file_study().config.study_path / "input/data-series/modeler-scenariobuilder.dat"
    # The test creates the input file directly, before calling the DAO.
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n  \n")
    assert dao.get_gems_scenario_builder() is None
    builder = GemsScenarioBuilder(scenarios={"load": [GemsScBuilderMapping(scenario=0, time_series_index=1)]})
    dao.save_gems_scenario_builder(builder)
    assert dao.get_gems_scenario_builder() == builder


def test_real_file_roundtrip(filestudy_dao_v10_2: FileStudyTreeDao) -> None:
    dao = filestudy_dao_v10_2
    path = dao.get_file_study().config.study_path / "input/data-series/modeler-scenariobuilder.dat"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(ASSET.read_bytes())
    builder = dao.get_gems_scenario_builder()
    assert builder is not None
    assert len(builder.scenarios) == 21
    expected_mapping = [
        GemsScBuilderMapping(scenario=0, time_series_index=1),
        GemsScBuilderMapping(scenario=1, time_series_index=2),
    ]
    assert all(mapping == expected_mapping for mapping in builder.scenarios.values())
    assert "thermal_area2_lignite_group" in builder.scenarios
    dao.save_gems_scenario_builder(builder)
    assert dao.get_gems_scenario_builder() == builder
    assert path.read_text().strip() == ASSET.read_text().strip()


@pytest.mark.parametrize(
    "line", ["load 0 = 1", "load, -1 = 1", "load, 0 = 0", "load, 0 = 1.5", ", 0 = 1", "load, 0 = 1\nload, 0 = 2"]
)
def test_invalid_file(filestudy_dao_v10_2: FileStudyTreeDao, line: str) -> None:
    path = filestudy_dao_v10_2.get_file_study().config.study_path / "input/data-series/modeler-scenariobuilder.dat"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(line)
    with pytest.raises(ValueError):
        filestudy_dao_v10_2.get_gems_scenario_builder()


def test_whitespace(filestudy_dao_v10_2: FileStudyTreeDao) -> None:
    path = filestudy_dao_v10_2.get_file_study().config.study_path / "input/data-series/modeler-scenariobuilder.dat"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n  Load_Group , 0 = 2 \n\nLoad_Group,3=5\n")
    assert filestudy_dao_v10_2.get_gems_scenario_builder() == GemsScenarioBuilder(
        scenarios={
            "Load_Group": [
                GemsScBuilderMapping(scenario=0, time_series_index=2),
                GemsScBuilderMapping(scenario=3, time_series_index=5),
            ]
        }
    )


@pytest.mark.parametrize("dao_10_2", ["db"], indirect=True)
@pytest.mark.parametrize("empty", [False, True])
@pytest.mark.parametrize("with_library", [False, True])
def test_conversion_roundtrip(
    dao_10_2: StudyDao,
    filestudy_dao_v10_2: FileStudyTreeDao,
    matrix_service: ISimpleMatrixService,
    empty: bool,
    with_library: bool,
) -> None:
    file_dao = filestudy_dao_v10_2
    if with_library:
        file_dao.save_library(GemsLibrary(id="test_library"))
    path = file_dao.get_file_study().config.study_path / "input/data-series/modeler-scenariobuilder.dat"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"" if empty else ASSET.read_bytes())
    builder = file_dao.get_gems_scenario_builder() if with_library else None
    StudyConverter(file_dao, dao_10_2, STUDY_VERSION_10_2, matrix_service).convert_study_inputs()
    assert dao_10_2.get_gems_scenario_builder() == builder
    path.unlink()
    (file_dao.get_file_study().config.study_path / "input/model-libraries/library.yaml").unlink(missing_ok=True)
    # Only GEMS is copied back: the destination already contains the legacy study inputs.
    StudyConverter(dao_10_2, file_dao, STUDY_VERSION_10_2, matrix_service)._convert_gems()
    assert file_dao.get_gems_scenario_builder() == builder
