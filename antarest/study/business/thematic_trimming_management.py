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


from antarest.study.business.model.thematic_trimming_model import ThematicTrimming, update_thematic_trimming
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.variantstudy.model.command.update_thematic_trimming import UpdateThematicTrimming
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class ThematicTrimmingManager:
    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_thematic_trimming(self, study: StudyInterface) -> ThematicTrimming:
        """
        Get Thematic Trimming field values for the webapp form
        """
        return study.get_study_dao().get_thematic_trimming()

    def set_thematic_trimming(self, study: StudyInterface, thematic_trimming: ThematicTrimming) -> ThematicTrimming:
        """
        Set Thematic Trimming config from the webapp form
        """
        current_thematic_trimming = self.get_thematic_trimming(study)
        final_thematic_trimming = update_thematic_trimming(current=current_thematic_trimming, new=thematic_trimming)

        command = UpdateThematicTrimming(
            parameters=thematic_trimming,
            command_context=self._command_context,
            study_version=study.version,
        )
        study.add_commands([command])

        return final_thematic_trimming
