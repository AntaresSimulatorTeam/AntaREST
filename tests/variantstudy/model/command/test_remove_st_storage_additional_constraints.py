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
from antarest.core.serde.ini_reader import read_ini
from antarest.study.business.model.sts_model import (
    STStorageAdditionalConstraintCreation,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_st_storage import CreateSTStorage
from antarest.study.storage.variantstudy.model.command.create_st_storage_constraints import (
    CreateSTStorageAdditionalConstraints,
)
from antarest.study.storage.variantstudy.model.command.remove_multiple_storage_constraints import (
    RemoveMultipleSTStorageConstraints,
)
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class TestRemoveSTStorageAdditionalConstraint:
    def test_nominal_case(self, command_context: CommandContext, empty_study_920: FileStudy):
        ####### Set Up ########
        study = empty_study_920
        version = study.config.version
        for area in ["fr", "de"]:
            cmd = CreateArea(area_name=area, command_context=command_context, study_version=study.config.version)
            cmd.apply(study)
            cmd = CreateSTStorage(
                area_id=area, parameters={"name": f"sts_{area}"}, command_context=command_context, study_version=version
            )
            cmd.apply(study_data=study)

        # Create several constraints
        cmd = CreateSTStorageAdditionalConstraints(
            command_context=command_context,
            area_id="fr",
            storage_id="sts_fr",
            constraints=[
                STStorageAdditionalConstraintCreation(name="constraint"),
                STStorageAdditionalConstraintCreation(name="constraint_2"),
                STStorageAdditionalConstraintCreation(name="constraint_3"),
            ],
            study_version=version,
        )
        output = cmd.apply(study)
        assert output.status

        # Removes several constraints
        cmd = RemoveMultipleSTStorageConstraints(
            command_context=command_context,
            area_id="fr",
            storage_id="sts_fr",
            ids=["constraint", "constraint_2"],
            study_version=version,
        )
        output = cmd.apply(study)
        assert output.status

        # Checks the ini content
        ini_path = (
            study.config.study_path
            / "input"
            / "st-storage"
            / "constraints"
            / "fr"
            / "sts_fr"
            / "additional-constraints.ini"
        )
        ini_content = read_ini(ini_path)
        assert ini_content == {
            "constraint_3": {
                "enabled": True,
                "hours": "[]",
                "operator": "less",
                "variable": "netting",
            }
        }

    def test_error_cases(self, command_context: CommandContext, empty_study_920: FileStudy):
        study = empty_study_920
        version = study.config.version

        # Removes a constraint in a fake area
        cmd = RemoveMultipleSTStorageConstraints(
            command_context=command_context,
            area_id="fr",
            storage_id="sts",
            ids=["constraint"],
            study_version=version,
        )
        output = cmd.apply(study)
        assert not output.status
        assert output.message == "Short-term storage constraint 'constraint' not found."

        # Create the area `fr`
        CreateArea(area_name="fr", command_context=command_context, study_version=study.config.version).apply(study)

        # Removes a fake constraint
        output = cmd.apply(study)
        assert not output.status
        assert output.message == "Short-term storage constraint 'constraint' not found."
