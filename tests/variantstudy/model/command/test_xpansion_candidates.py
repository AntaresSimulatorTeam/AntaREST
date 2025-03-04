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
from study.storage.variantstudy.model.command.create_area import CreateArea
from study.storage.variantstudy.model.command.create_link import CreateLink
from study.storage.variantstudy.model.command.create_xpansion_candidate import CreateXpansionCandidate

from antarest.study.business.model.xpansion_model import XpansionCandidateInternal
from antarest.study.model import STUDY_VERSION_8_7
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.update_xpansion_candidate import UpdateXpansionCandidate
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class TestXpansionCandidate:
    @staticmethod
    def set_up(empty_study: FileStudy, command_context: CommandContext):
        # Creates a link for candidates
        cmd = CreateArea(command_context=command_context, area_name="at", study_version=STUDY_VERSION_8_7)
        cmd.apply(study_data=empty_study)
        cmd = CreateArea(command_context=command_context, area_name="be", study_version=STUDY_VERSION_8_7)
        cmd.apply(study_data=empty_study)
        cmd = CreateLink(area1="at", area2="be", command_context=command_context, study_version=STUDY_VERSION_8_7)
        cmd.apply(study_data=empty_study)

        # Creates a default xpansion configuration
        empty_study.tree.save(
            {"user": {"expansion": {"capa": {}, "weights": {}, "constraints": {}, "settings": {}, "candidates": {}}}}
        )

        # Creates capacity files for candidates
        xpansion_path = empty_study.config.study_path / "user" / "expansion"
        (xpansion_path / "capa" / "capa1.txt").touch()
        (xpansion_path / "capa" / "capa2.txt").touch()
        (xpansion_path / "capa" / "capa3.txt").touch()
        (xpansion_path / "capa" / "capa4.txt").touch()

    @pytest.mark.parametrize("empty_study", ["empty_study_870.zip"], indirect=True)
    def test_nominal_case(self, empty_study: FileStudy, command_context: CommandContext):
        self.set_up(empty_study, command_context)

        # Creates 2 candidates
        cmd = CreateXpansionCandidate(
            candidate=XpansionCandidateInternal(
                name="cdt_1", link="at - be", annual_cost_per_mw=12, max_investment=100
            ),
            command_context=command_context,
            study_version=STUDY_VERSION_8_7,
        )
        output = cmd.apply(study_data=empty_study)
        assert output.status, output.message

        cmd = CreateXpansionCandidate(
            candidate=XpansionCandidateInternal(
                name="cdt_2", link="at - be", annual_cost_per_mw=156, max_units=7, unit_size=19
            ),
            command_context=command_context,
            study_version=STUDY_VERSION_8_7,
        )
        output = cmd.apply(study_data=empty_study)
        assert output.status, output.message

        # Updates one
        cmd = UpdateXpansionCandidate(
            candidate_name="cdt_1",
            new_properties=XpansionCandidateInternal(
                name="cdt_1", link="at - be", annual_cost_per_mw=30, max_investment=100, direct_link_profile="capa1.txt"
            ),
            command_context=command_context,
            study_version=STUDY_VERSION_8_7,
        )
        output = cmd.apply(study_data=empty_study)
        assert output.status, output.message

        # Removes one and assert the other still exist

    @pytest.mark.parametrize("empty_study", ["empty_study_870.zip"], indirect=True)
    def test_error_cases(self, empty_study: FileStudy, command_context: CommandContext):
        self.set_up(empty_study, command_context)

        # Creates wrongly formatted candidate

        # Create a candidate with an already taken name

        # Create a candidate on a fake link

        # Create a candidate with a fake capa registered

        # Rename a candidate with an already taken name

        # Update a candidate with wrongly formatted parameters

        # Removes a candidate that doesn't exist
