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
from unittest.mock import ANY

from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.replace_study_author import ReplaceStudyAuthor
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class TestReplaceStudyAuthor:
    def test_nominal_case(self, empty_study_880: FileStudy, command_context: CommandContext):
        study = empty_study_880
        content = study.tree.get(["study"])
        assert content == {
            "antares": {
                "version": 880,
                "caption": "empty_study",
                "author": "Unknown",
                "editor": "Unknown",
                "created": ANY,
                "lastsave": ANY,
            }
        }

        command = ReplaceStudyAuthor(
            author="John Doe", command_context=command_context, study_version=study.config.version
        )
        output = command.apply(study_data=study)
        assert output.status

        content = study.tree.get(["study"])
        assert content == {
            "antares": {
                "version": 880,
                "caption": "empty_study",
                "author": "John Doe",
                "editor": "John Doe",
                "created": ANY,
                "lastsave": ANY,
            }
        }
