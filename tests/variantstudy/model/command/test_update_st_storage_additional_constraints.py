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

from antarest.study.business.model.sts_model import (
    AdditionalConstraintOperator,
    AdditionalConstraintVariable,
    STStorageAdditionalConstraintCreation,
    STStorageAdditionalConstraintUpdate,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_st_storage import CreateSTStorage
from antarest.study.storage.variantstudy.model.command.create_st_storage_constraints import (
    CreateSTStorageAdditionalConstraints,
)
from antarest.study.storage.variantstudy.model.command.update_st_storage_additional_constraints import (
    UpdateSTStorageAdditionalConstraints,
)
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class TestUpdateSTStorageAdditionalConstraint:
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
                STStorageAdditionalConstraintCreation(name="constraint_2", hours=[2, 4], enabled=False),
            ],
            study_version=version,
        )
        output = cmd.apply(study)
        assert output.status

        cmd = CreateSTStorageAdditionalConstraints(
            command_context=command_context,
            area_id="de",
            storage_id="sts_de",
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

        # Update several constraints
        cmd = UpdateSTStorageAdditionalConstraints(
            command_context=command_context,
            additional_constraint_properties={
                "fr": {
                    "sts_fr": [
                        STStorageAdditionalConstraintUpdate(
                            id="constraint",
                            variable=AdditionalConstraintVariable.WITHDRAWAL,
                            hours=[[5, 6, 7], [167, 168]],
                        ),
                    ]
                },
                "de": {
                    "sts_de": [
                        STStorageAdditionalConstraintUpdate(
                            id="c3", enabled=False, operator=AdditionalConstraintOperator.EQUAL
                        )
                    ]
                },
            },
            study_version=version,
        )
        output = cmd.apply(study)
        assert output.status

        # Checks the ini content

    def test_error_cases(self, command_context: CommandContext, empty_study_920: FileStudy):
        study = empty_study_920
        version = study.config.version

        # Update a constraint in a fake area
        cmd = UpdateSTStorageAdditionalConstraints(
            command_context=command_context,
            additional_constraint_properties={"fr": {"sts_1": [STStorageAdditionalConstraintUpdate(id="constraint")]}},
            study_version=version,
        )
        output = cmd.apply(study)
        assert not output.status
        assert output.message == "The area 'fr' is not found."

        # Create the area `fr`
        cmd = CreateArea(area_name="fr", command_context=command_context, study_version=study.config.version)
        cmd.apply(study)

        # Update a constraint with a fake storage
        cmd = UpdateSTStorageAdditionalConstraints(
            command_context=command_context,
            additional_constraint_properties={"fr": {"sts_1": [STStorageAdditionalConstraintUpdate(id="constraint")]}},
            study_version=version,
        )
        output = cmd.apply(study)
        assert not output.status

        # Create the storage `sts_1`
        CreateSTStorage(
            area_id="fr", parameters={"name": "sts_1"}, command_context=command_context, study_version=version
        ).apply(study_data=study)

        # Create a constraint
        CreateSTStorageAdditionalConstraints(
            command_context=command_context,
            area_id="fr",
            storage_id="sts_1",
            constraints=[STStorageAdditionalConstraintCreation(name="constraint")],
            study_version=version,
        ).apply(study)

        # Update a fake constraint
        cmd = UpdateSTStorageAdditionalConstraints(
            command_context=command_context,
            additional_constraint_properties={"fr": {"sts_1": [STStorageAdditionalConstraintUpdate(id="fake")]}},
            study_version=version,
        )
        output = cmd.apply(study)
        assert not output.status
        assert output.message == "Constraint fake not found for short-term storage sts_1 in area 'fr'."
