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
from study.storage.rawstudy.model.filesystem.factory import FileStudy
from study.storage.variantstudy.model.command.create_area import CreateArea
from study.storage.variantstudy.model.command.create_st_storage import CreateSTStorage
from study.storage.variantstudy.model.command_context import CommandContext


class TestUpdateHydroManagement:
    def _set_up(self, study: FileStudy, command_context: CommandContext):
        CreateArea(area_name="FR", command_context=command_context, study_version=study.config.version).apply(study)
        CreateSTStorage(
            area_id="fr",
            parameters={"name": "STORAGE_1"},
            command_context=command_context,
            study_version=study.config.version,
        ).apply(study)

    @pytest.mark.parametrize("empty_study", ["empty_study_870.zip"], indirect=True)
    def test_nominal_case(self, empty_study: FileStudy, command_context: CommandContext):
        pass
