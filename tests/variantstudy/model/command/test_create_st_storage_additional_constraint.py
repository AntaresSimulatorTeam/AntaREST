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


from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_st_storage_constraints import (
    CreateSTStorageAdditionalConstraints,
)
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class TestCreateSTStorageAdditionalConstraint:
    def test_nominal_case(self, command_context: CommandContext, empty_study_920: FileStudy):
        pass

    def test_error_cases(self, command_context: CommandContext, empty_study_920: FileStudy):
        study = empty_study_920
        version = study.config.version

        # Create a constraint in a fake area
        cmd = CreateSTStorageAdditionalConstraints(
            command_context=command_context,
            area_id="fr",
            storage_id="sts_1",
            constraints=[{"name": "constraint"}],
            study_version=version,
        )
        output = cmd.apply(study)
        assert not output.status
        assert output.message == "Short-term storage 'sts_1' inside area 'fr' does not exist."

        # Create the area `fr`
        cmd = CreateArea(area_name="fr", command_context=command_context, study_version=study.config.version)
        cmd.apply(study)

        # Create a constraint with a fake storage
        cmd = CreateSTStorageAdditionalConstraints(
            command_context=command_context,
            area_id="fr",
            storage_id="fake_storage",
            constraints=[{"name": "constraint"}],
            study_version=version,
        )
        output = cmd.apply(study)
        assert not output.status
        assert output.message == "Short-term storage 'fake_storage' inside area 'fr' does not exist."
