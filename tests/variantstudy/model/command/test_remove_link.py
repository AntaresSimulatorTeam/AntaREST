# Copyright (c) 2025, RTE (https://www.rte-france.com)
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

import os
import typing as t
import uuid
from pathlib import Path
from unittest.mock import Mock
from zipfile import ZipFile

import pytest
from checksumdir import dirhash
from pydantic import ValidationError

from antarest.study.model import STUDY_VERSION_8_8
from antarest.study.storage.rawstudy.model.filesystem.config.files import build
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import FileStudyTree
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_link import CreateLink
from antarest.study.storage.variantstudy.model.command.remove_link import RemoveLink
from antarest.study.storage.variantstudy.model.command.update_scenario_builder import UpdateScenarioBuilder
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from tests.variantstudy.model.command.helpers import reset_line_separator


class TestRemoveLink:
    @pytest.mark.parametrize(
        "area1, area2, expected",
        [
            pytest.param(
                "",
                "",
                {},
                id="not-empty-areas",
                marks=pytest.mark.xfail(reason="Area IDs must not be empty", raises=ValidationError, strict=True),
            ),
            pytest.param(
                None,
                None,
                {},
                id="not-none-areas",
                marks=pytest.mark.xfail(reason="Area IDs must not be None", raises=ValidationError, strict=True),
            ),
            pytest.param(
                "%!",
                "~#é",
                {},
                id="invalid-areas",
                marks=pytest.mark.xfail(reason="Invalid characters", raises=ValidationError, strict=True),
            ),
            pytest.param("Zone1", "Zone2", {"area1": "zone1", "area2": "zone2"}, id="area-to-lowercase"),
            pytest.param("TO", "FROM", {"area1": "from", "area2": "to"}, id="areas-reordered"),
        ],
    )
    def test_remove_link__validation(self, area1: str, area2: str, expected: t.Dict[str, str]) -> None:
        """
        This test checks that the parameters control (the area names) is done correctly.
        It checks that the area names are correctly converted to area ID (in lowercase)
        and that the areas are well-ordered in alphabetical order (Antares Solver convention).
        """
        command = RemoveLink(
            area1=area1, area2=area2, command_context=Mock(spec=CommandContext), study_version=STUDY_VERSION_8_8
        )
        actual = command.model_dump(include={"area1", "area2"})
        assert actual == expected

    @staticmethod
    def make_study(tmpdir: Path, version: int) -> FileStudy:
        study_dir: Path = (
            Path(__file__).parent.parent.parent.parent
            / "storage"
            / "business"
            / "assets"
            / f"empty_study_{version}.zip"
        )
        study_path = Path(tmpdir / str(uuid.uuid4()))
        os.mkdir(study_path)
        with ZipFile(study_dir) as zip_output:
            zip_output.extractall(path=study_path)
        config = build(study_path, "1")
        return FileStudy(config, FileStudyTree(Mock(), config))

    @pytest.mark.parametrize("version", [810, 820])
    def test_apply(self, tmpdir: Path, command_context: CommandContext, version: int) -> None:
        empty_study = self.make_study(tmpdir, version)
        study_version = empty_study.config.version

        # Create some areas
        areas = {transform_name_to_id(area, lower=True): area for area in ["Area_X", "Area_Y", "Area_Z"]}
        for area in areas.values():
            output = CreateArea(area_name=area, command_context=command_context, study_version=study_version).apply(
                empty_study
            )
            assert output.status, output.message

        # Create a link between Area_X and Area_Y
        output = CreateLink(
            area1="area_x", area2="area_y", command_context=command_context, study_version=study_version
        ).apply(empty_study)
        assert output.status, output.message

        # Create a ruleset in the Scenario Builder configuration for this link
        output = UpdateScenarioBuilder(
            data={"Default Ruleset": {"ntc,area_x,area_y,0": 1}},
            command_context=command_context,
            study_version=study_version,
        ).apply(study_data=empty_study)
        assert output.status, output.message

        ########################################################################################

        # Line ending of the `settings/scenariobuilder.dat` must be reset before checksum
        reset_line_separator(empty_study.config.study_path.joinpath("settings/scenariobuilder.dat"))
        hash_before_removal = dirhash(empty_study.config.study_path, "md5")

        # Create a link between Area_X and Area_Z
        output = CreateLink(
            area1="area_x", area2="area_z", command_context=command_context, study_version=study_version
        ).apply(empty_study)
        assert output.status, output.message

        # Create a ruleset in the Scenario Builder configuration for this link
        output = UpdateScenarioBuilder(
            data={"Default Ruleset": {"ntc,area_x,area_z,0": 1}},
            command_context=command_context,
            study_version=study_version,
        ).apply(study_data=empty_study)
        assert output.status, output.message

        output = RemoveLink(
            area1="area_x", area2="area_z", command_context=command_context, study_version=study_version
        ).apply(empty_study)
        assert output.status, output.message

        assert dirhash(empty_study.config.study_path, "md5") == hash_before_removal
