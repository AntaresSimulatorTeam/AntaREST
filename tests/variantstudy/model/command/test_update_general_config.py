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
from antarest.study.business.model.config.general_model import GeneralConfigUpdate
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.update_general_config import UpdateGeneralConfig
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class TestUpdateGeneralConfig:
    def test_update_general_config(self, empty_study_880: FileStudy, command_context: CommandContext):
        study = empty_study_880

        default_values = study.tree.get(["settings", "generaldata", "general"])

        args = {
            "horizon": "2030",
        }

        properties = GeneralConfigUpdate.model_validate(args)

        command = UpdateGeneralConfig(
            parameters=properties, command_context=command_context, study_version=study.config.version
        )
        output = command.apply(study_data=study)
        assert output.status
        default_values.update({"horizon": 2030, "building_mode": "automatic"})

        general_config = study.tree.get(["settings", "generaldata", "general"])

        assert general_config == default_values
