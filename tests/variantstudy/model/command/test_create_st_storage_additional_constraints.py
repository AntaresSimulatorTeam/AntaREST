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

from antarest.core.serde.ini_reader import read_ini
from antarest.study.business.model.sts_model import (
    AdditionalConstraintOperator,
    AdditionalConstraintVariable,
    STStorageAdditionalConstraintCreation,
)
from antarest.study.model import STUDY_VERSION_8_8
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_st_storage import CreateSTStorage
from antarest.study.storage.variantstudy.model.command.create_st_storage_constraints import (
    CreateSTStorageAdditionalConstraints,
)
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class TestCreateSTStorageAdditionalConstraint:
    def test_nominal_case(self, command_context: CommandContext, empty_study_920: FileStudy):
        # Set Up
        study = empty_study_920
        version = study.config.version
        cmd = CreateArea(area_name="fr", command_context=command_context, study_version=study.config.version)
        cmd.apply(study)
        for name in ["sts_1", "sts_2"]:
            cmd = CreateSTStorage(
                area_id="fr", parameters={"name": name}, command_context=command_context, study_version=version
            )
            cmd.apply(study_data=study)

        # Create several constraints
        cmd = CreateSTStorageAdditionalConstraints(
            command_context=command_context,
            area_id="fr",
            storage_id="sts_1",
            constraints=[
                STStorageAdditionalConstraintCreation(name="Constraint??"),
                STStorageAdditionalConstraintCreation(name="constraint_2", hours=[[2, 4]], enabled=False),
            ],
            study_version=version,
        )
        output = cmd.apply(study)
        assert output.status

        # Create another one referencing the other storage
        cmd = CreateSTStorageAdditionalConstraints(
            command_context=command_context,
            area_id="fr",
            storage_id="sts_2",
            constraints=[
                STStorageAdditionalConstraintCreation(
                    name="c3",
                    variable=AdditionalConstraintVariable.WITHDRAWAL,
                    operator=AdditionalConstraintOperator.GREATER,
                    hours=[[1, 2, 3, 4], [12, 13]],
                )
            ],
            study_version=version,
        )
        output = cmd.apply(study)
        assert output.status

        # Checks the ini content
        constraints_path = study.config.study_path / "input" / "st-storage" / "constraints" / "fr"
        ini_path = constraints_path / "sts_1" / "additional-constraints.ini"
        ini_content = read_ini(ini_path)
        assert ini_content == {
            "Constraint??": {
                "variable": "netting",
                "operator": "less",
                "hours": "[]",
                "enabled": True,
            },
            "constraint_2": {
                "variable": "netting",
                "operator": "less",
                "hours": "[2, 4]",
                "enabled": False,
            },
        }
        ini_path = constraints_path / "sts_2" / "additional-constraints.ini"
        ini_content = read_ini(ini_path)
        assert ini_content == {
            "c3": {
                "variable": "withdrawal",
                "operator": "greater",
                "hours": "[1, 2, 3, 4], [12, 13]",
                "enabled": True,
            },
        }

    def test_error_cases(self, command_context: CommandContext, empty_study_920: FileStudy):
        study = empty_study_920
        version = study.config.version

        # Create a constraint in a fake area
        cmd = CreateSTStorageAdditionalConstraints(
            command_context=command_context,
            area_id="fr",
            storage_id="sts_1",
            constraints=[STStorageAdditionalConstraintCreation(name="constraint")],
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
            constraints=[STStorageAdditionalConstraintCreation(name="constraint")],
            study_version=version,
        )
        output = cmd.apply(study)
        assert not output.status
        assert output.message == "Short-term storage 'fake_storage' inside area 'fr' does not exist."

        # Create the storage `sts_1`
        cmd = CreateSTStorage(
            area_id="fr", parameters={"name": "sts_1"}, command_context=command_context, study_version=version
        )
        cmd.apply(study_data=study)

        # Create a constraint
        cmd = CreateSTStorageAdditionalConstraints(
            command_context=command_context,
            area_id="fr",
            storage_id="sts_1",
            constraints=[STStorageAdditionalConstraintCreation(name="constraint")],
            study_version=version,
        )
        output = cmd.apply(study)
        assert output.status

        # Create a constraint with the same name
        output = cmd.apply(study)
        assert not output.status
        assert output.message == "Short-term storage constraint 'constraint' already exists."

        # Create a constraint with an old study
        with pytest.raises(
            ValueError,
            match="Command 'create_st_storage_additional_constraints' is only available since v9.2 and you're in 8.8",
        ):
            CreateSTStorageAdditionalConstraints(
                command_context=command_context,
                area_id="fr",
                storage_id="sts_1",
                constraints=[STStorageAdditionalConstraintCreation(name="constraint")],
                study_version=STUDY_VERSION_8_8,
            )

        # Create an object `STStorageAdditionalConstraintCreation` with wrong `hours`
        with pytest.raises(ValueError, match="Hours must be integers between 0 and 168, got 173"):
            STStorageAdditionalConstraintCreation(name="c1", hours=[[173]])

        # Create 2 constraints with the same id in the same area
        cmd = CreateSTStorageAdditionalConstraints(
            command_context=command_context,
            area_id="fr",
            storage_id="sts_1",
            constraints=[
                STStorageAdditionalConstraintCreation(name="constraint"),
                STStorageAdditionalConstraintCreation(name="Constraint???"),
            ],
            study_version=version,
        )
        output = cmd.apply(study)
        assert not output.status
        assert output.message == "Several constraints with the same id 'constraint' were given"
