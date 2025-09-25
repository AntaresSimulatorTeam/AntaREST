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

from antarest.study.business.model.xpansion_model import (
    XpansionAdequacyCriterion,
    XpansionAdequacyPattern,
    XpansionSecurityCriterionUpdate,
)
from antarest.study.model import STUDY_VERSION_8_7
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.update_xpansion_security_criterion import (
    UpdateXpansionSecurityCriterion,
)
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class TestUpdateXpansionSettings:
    @staticmethod
    def set_up(empty_study: FileStudy, command_context: CommandContext):
        empty_study.tree.save(
            {
                "user": {
                    "expansion": {
                        "capa": {},
                        "weights": {},
                        "constraints": {},
                        "settings": {},
                        "candidates": {},
                        "adequacy_criterion": {
                            "adequacy_criterion": {"stopping_threshold": 3, "criterion_count_threshold": 1.2}
                        },
                    }
                }
            }
        )
        cmd1 = CreateArea(area_name="FR", command_context=command_context, study_version=empty_study.config.version)
        cmd2 = CreateArea(area_name="de", command_context=command_context, study_version=empty_study.config.version)
        cmd1.apply(empty_study)
        cmd2.apply(empty_study)

    def test_nominal_case(self, empty_study_870: FileStudy, command_context: CommandContext):
        empty_study = empty_study_870
        self.set_up(empty_study, command_context)

        # Add some patterns
        new_criterion = XpansionSecurityCriterionUpdate(
            patterns=[
                XpansionAdequacyPattern(area="fr", criterion=2.3),
                XpansionAdequacyPattern(area="de", criterion=11),
            ]
        )
        cmd = UpdateXpansionSecurityCriterion(
            criterion=new_criterion,
            command_context=command_context,
            study_version=STUDY_VERSION_8_7,
        )
        output = cmd.apply(study_data=empty_study)
        assert output.status, output.message

        # Checks the file content
        file_path = (
            empty_study.config.study_path / "user" / "expansion" / "adequacy_criterion" / "adequacy_criterion.yml"
        )
        assert (
            file_path.read_text()
            == """criterion_count_threshold: 1.2
patterns:
- area: fr
  criterion: 2.3
- area: de
  criterion: 11.0
stopping_threshold: 3.0
"""
        )

        # Modify the criterion_count_threshold only
        cmd = UpdateXpansionSecurityCriterion(
            criterion=XpansionSecurityCriterionUpdate(criterion_count_threshold=4),
            command_context=command_context,
            study_version=STUDY_VERSION_8_7,
        )
        output = cmd.apply(study_data=empty_study)
        assert output.status, output.message

        # Checks the file content
        assert (
            file_path.read_text()
            == """criterion_count_threshold: 4.0
patterns:
- area: fr
  criterion: 2.3
- area: de
  criterion: 11.0
stopping_threshold: 3.0
"""
        )

        # Removes a pattern
        cmd = UpdateXpansionSecurityCriterion(
            criterion=XpansionSecurityCriterionUpdate(patterns=[XpansionAdequacyPattern(area="fr", criterion=6.1)]),
            command_context=command_context,
            study_version=STUDY_VERSION_8_7,
        )
        output = cmd.apply(study_data=empty_study)
        assert output.status, output.message

        # Checks the file content
        assert (
            file_path.read_text()
            == """criterion_count_threshold: 4.0
patterns:
- area: fr
  criterion: 6.1
stopping_threshold: 3.0
"""
        )

    def test_error_cases(self, empty_study_870: FileStudy, command_context: CommandContext):
        empty_study = empty_study_870
        self.set_up(empty_study, command_context)

        # Try to update with a non-existing area
        cmd = UpdateXpansionSecurityCriterion(
            criterion=XpansionSecurityCriterionUpdate(patterns=[XpansionAdequacyPattern(area="fake", criterion=6.1)]),
            command_context=command_context,
            study_version=STUDY_VERSION_8_7,
        )
        output = cmd.apply(study_data=empty_study)
        assert output.status is False
        assert "Area is not found: 'fake'" in output.message

        # Try to give wrong values for the criterion parameters
        with pytest.raises(ValueError, match="Input should be greater than or equal to 0"):
            XpansionAdequacyCriterion(stopping_threshold=-2)

        with pytest.raises(ValueError, match="Input should be greater than or equal to 0"):
            XpansionAdequacyCriterion(criterion_count_threshold=-2)

        with pytest.raises(ValueError, match="Input should be greater than or equal to 0"):
            XpansionAdequacyPattern(area="fake", criterion=-2)
