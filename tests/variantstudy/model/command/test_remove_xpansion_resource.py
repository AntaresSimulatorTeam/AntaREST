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

import pytest

from antarest.study.business.model.xpansion_model import XpansionResourceFileType
from antarest.study.model import STUDY_VERSION_8_7
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.remove_xpansion_resource import RemoveXpansionResource
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class TestRemoveXpansionResource:
    @staticmethod
    def set_up(empty_study: FileStudy):
        empty_study.tree.save(
            {"user": {"expansion": {"capa": {}, "weights": {}, "constraints": {}, "settings": {}, "candidates": {}}}}
        )
        study_path = empty_study.config.study_path
        xpansion_path = study_path / "user" / "expansion"

        (xpansion_path / "capa" / "capa1.txt").touch()
        (xpansion_path / "capa" / "capa2.txt").touch()

        (xpansion_path / "weights" / "weights1.txt").touch()
        (xpansion_path / "weights" / "weights2.txt").touch()

        (xpansion_path / "constraints" / "constraints1.ini").touch()
        (xpansion_path / "constraints" / "constraints2.txt").touch()

    @pytest.mark.parametrize("empty_study", STUDY_VERSION_8_7, indirect=True)
    def test_nominal_case(self, empty_study: FileStudy, command_context: CommandContext):
        self.set_up(empty_study)

        # Constraints
        for file_name in ["constraints1.ini", "constraints2.txt"]:
            cmd = RemoveXpansionResource(
                resource_type=XpansionResourceFileType.CONSTRAINTS,
                filename=file_name,
                command_context=command_context,
                study_version=STUDY_VERSION_8_7,
            )
            output = cmd.apply(study_data=empty_study)
            assert output.status, output.message
            resource_path = empty_study.config.study_path / "user" / "expansion" / "constraints" / file_name
            assert not resource_path.exists()

        # Weights
        for file_name in ["weights1.txt", "weights2.txt"]:
            cmd = RemoveXpansionResource(
                resource_type=XpansionResourceFileType.WEIGHTS,
                filename=file_name,
                command_context=command_context,
                study_version=STUDY_VERSION_8_7,
            )
            output = cmd.apply(study_data=empty_study)
            assert output.status, output.message
            resource_path = empty_study.config.study_path / "user" / "expansion" / "weights" / file_name
            assert not resource_path.exists()

        # Capa
        for file_name in ["capa1.txt", "capa2.txt"]:
            cmd = RemoveXpansionResource(
                resource_type=XpansionResourceFileType.CAPACITIES,
                filename=file_name,
                command_context=command_context,
                study_version=STUDY_VERSION_8_7,
            )
            output = cmd.apply(study_data=empty_study)
            assert output.status, output.message
            resource_path = empty_study.config.study_path / "user" / "expansion" / "capa" / file_name
            assert not resource_path.exists()

    @pytest.mark.parametrize("empty_study", STUDY_VERSION_8_7, indirect=True)
    def test_error_case_for_constraint(self, empty_study: FileStudy, command_context: CommandContext):
        self.set_up(empty_study)
        file_name = "constraints1"

        settings_file = empty_study.config.path / "user" / "expansion" / "settings.ini"
        with open(settings_file, "w") as f:
            f.write(f"additional-constraints = {file_name}")

        cmd = RemoveXpansionResource(
            resource_type=XpansionResourceFileType.CONSTRAINTS,
            filename=file_name,
            command_context=command_context,
            study_version=STUDY_VERSION_8_7,
        )
        output = cmd.apply(study_data=empty_study)
        assert output.status is False
        assert (
            f"The constraints file '{file_name}' is still used in the xpansion settings and cannot be deleted"
            in output.message
        )

    @pytest.mark.parametrize("empty_study", ["empty_study_870.zip"], indirect=True)
    def test_error_case_for_weight(self, empty_study: FileStudy, command_context: CommandContext):
        self.set_up(empty_study)
        file_name = "weights1"

        settings_file = empty_study.config.path / "user" / "expansion" / "settings.ini"
        with open(settings_file, "w") as f:
            f.write(f"yearly-weights = {file_name}")

        cmd = RemoveXpansionResource(
            resource_type=XpansionResourceFileType.WEIGHTS,
            filename=file_name,
            command_context=command_context,
            study_version=STUDY_VERSION_8_7,
        )
        output = cmd.apply(study_data=empty_study)
        assert output.status is False
        assert (
            f"The weights file '{file_name}' is still used in the xpansion settings and cannot be deleted"
            in output.message
        )

    @pytest.mark.parametrize("empty_study", ["empty_study_870.zip"], indirect=True)
    def test_error_case_for_capa(self, empty_study: FileStudy, command_context: CommandContext):
        self.set_up(empty_study)
        file_name = "capa1"

        settings_file = empty_study.config.path / "user" / "expansion" / "candidates.ini"
        with open(settings_file, "w") as f:
            f.write(f"[0]\nlink-profile = {file_name}")

        cmd = RemoveXpansionResource(
            resource_type=XpansionResourceFileType.CAPACITIES,
            filename=file_name,
            command_context=command_context,
            study_version=STUDY_VERSION_8_7,
        )
        output = cmd.apply(study_data=empty_study)
        assert output.status is False
        assert (
            f"The capacities file '{file_name}' is still used in the xpansion settings and cannot be deleted"
            in output.message
        )
