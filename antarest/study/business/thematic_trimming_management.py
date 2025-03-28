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


from antarest.study.business.model.thematic_trimming_model import ThematicTrimming
from antarest.study.business.study_interface import StudyInterface
from antarest.study.business.utils import GENERAL_DATA_PATH
from antarest.study.storage.rawstudy.model.filesystem.config.thematic_trimming import (
    parse_thematic_trimming,
    serialize_thematic_trimming,
)
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class ThematicTrimmingManager:
    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_field_values(self, study: StudyInterface) -> ThematicTrimming:
        """
        Get Thematic Trimming field values for the webapp form
        """
        file_study = study.get_files()
        config = file_study.tree.get(GENERAL_DATA_PATH.split("/"))
        trimming_config = config.get("variables selection") or {}
        return parse_thematic_trimming(study.version, trimming_config)

    def set_field_values(self, study: StudyInterface, thematic_trimming: ThematicTrimming) -> None:
        """
        Set Thematic Trimming config from the webapp form
        """
        data = serialize_thematic_trimming(study.version, thematic_trimming)

        command = UpdateConfig(
            target="settings/generaldata/variables selection",
            data=data,
            command_context=self._command_context,
            study_version=study.version,
        )
        study.add_commands([command])
