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

import datetime
import typing as t
import uuid
from pathlib import Path

import pytest
from antares.study.version import StudyVersion
from sqlalchemy import event

from antarest.core.jwt import JWTGroup, JWTUser
from antarest.core.model import PublicMode
from antarest.core.roles import RoleType
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.login.model import Group, Role, User
from antarest.study.model import RawStudy, StudyAdditionalData
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from antarest.study.storage.variantstudy.model.model import CommandDTO, CommandDTOAPI
from antarest.study.storage.variantstudy.snapshot_generator import SnapshotGenerator
from antarest.study.storage.variantstudy.variant_study_service import VariantStudyService
from tests.helpers import AnyUUID, with_db_context


class TestVariantStudyService:
    @pytest.fixture(name="jwt_user")
    def jwt_user_fixture(self) -> JWTUser:
        # Create a user in a "Writers" group:
        jwt_user = JWTUser(
            id=7,
            impersonator=7,
            type="users",
            groups=[JWTGroup(id="writers", name="Writers", role=RoleType.WRITER)],
        )
        # Ensure the user is in database.
        with db():
            role = Role(
                type=RoleType.WRITER,
                identity=User(id=jwt_user.id, name="john.doe"),
                group=Group(id="writers"),
            )
            db.session.add(role)
            db.session.commit()
        return jwt_user

    @pytest.fixture(name="root_study_id")
    def root_study_id_fixture(
        self,
        tmp_path: Path,
        raw_study_service: RawStudyService,
        variant_study_service: VariantStudyService,
        jwt_user: JWTUser,
        request: t.Any,
    ) -> str:
        # Get public mode argument
        public_mode = request.param

        # Prepare a RAW study in the temporary folder
        study_dir = tmp_path / "my-study"
        root_study_id = str(uuid.uuid4())
        root_study = RawStudy(
            id=root_study_id,
            workspace="default",
            path=str(study_dir),
            version="860",
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow(),
            additional_data=StudyAdditionalData(author="john.doe"),
            owner_id=jwt_user.id,
            public_mode=PublicMode.EDIT if public_mode else PublicMode.NONE,
        )
        root_study = raw_study_service.create(root_study)
        with db():
            # Save the root study in database
            variant_study_service.repository.save(root_study)
        return root_study_id

    @pytest.mark.parametrize("root_study_id", [False], indirect=True)
    @with_db_context
    def test_commands_service(
        self,
        root_study_id: str,
        jwt_user: JWTUser,
        generator_matrix_constants: GeneratorMatrixConstants,
        variant_study_service: VariantStudyService,
    ) -> None:
        # Create a new variant
        variant_study = variant_study_service.create_variant_study(root_study_id, "my-variant")
        study_version = StudyVersion.parse(variant_study.version)
        saved_id = variant_study.id
        study = variant_study_service.repository.get(saved_id)
        assert study is not None
        assert study.id == saved_id
        assert study.parent_id == root_study_id

        # Append commands one at the time
        command_count = 0
        command_1 = CommandDTO(action="create_area", args={"area_name": "Yes"}, study_version=study_version)
        variant_study_service.append_command(saved_id, command_1)
        command_count += 1

        command_2 = CommandDTO(action="create_area", args={"area_name": "No"}, study_version=study_version)
        variant_study_service.append_command(saved_id, command_2)
        command_count += 1

        commands = variant_study_service.get_commands(saved_id)
        assert len(commands) == command_count

        # Append multiple commands
        command_3 = CommandDTO(action="create_area", args={"area_name": "Maybe"}, study_version=study_version)
        command_4 = CommandDTO(action="create_link", args={"area1": "no", "area2": "yes"}, study_version=study_version)
        variant_study_service.append_commands(saved_id, [command_3, command_4])
        command_count += 2

        commands = variant_study_service.get_commands(saved_id)
        assert len(commands) == command_count

        # Get command
        assert commands[0] == CommandDTOAPI.model_validate(
            variant_study_service.get_command(saved_id, commands[0].id).model_dump(
                mode="json", exclude={"study_version"}
            )
        )

        # Remove command (area "Maybe")
        variant_study_service.remove_command(saved_id, commands[2].id)
        command_count -= 1

        # Create a thermal cluster in the area "Yes"
        command_5 = CommandDTO(
            action="create_cluster",
            args={
                "area_id": "yes",
                "cluster_name": "cl1",
                "parameters": {"group": "Gas", "unitcount": 1, "nominalcapacity": 500},
            },
            study_version=study_version,
        )
        variant_study_service.append_command(saved_id, command_5)
        command_count += 1

        commands = variant_study_service.get_commands(saved_id)
        assert len(commands) == command_count

        # Generate using the SnapshotGenerator
        generator = SnapshotGenerator(
            cache=variant_study_service.cache,
            raw_study_service=variant_study_service.raw_study_service,
            command_factory=variant_study_service.command_factory,
            study_factory=variant_study_service.study_factory,
            repository=variant_study_service.repository,
        )
        results = generator.generate_snapshot(saved_id, jwt_user, denormalize=False)
        assert results.model_dump() == {
            "success": True,
            "details": [
                {
                    "id": AnyUUID(),
                    "name": "create_area",
                    "status": True,
                    "msg": "Area 'Yes' created",
                },
                {
                    "id": AnyUUID(),
                    "name": "create_area",
                    "status": True,
                    "msg": "Area 'No' created",
                },
                {
                    "id": AnyUUID(),
                    "name": "create_link",
                    "status": True,
                    "msg": "Link between 'no' and 'yes' created",
                },
                {
                    "id": AnyUUID(),
                    "name": "create_cluster",
                    "status": True,
                    "msg": "Thermal cluster 'cl1' added to area 'yes'.",
                },
            ],
        }
        assert study.snapshot.id == study.id

    @pytest.mark.parametrize("root_study_id", [True], indirect=True)
    @with_db_context
    def test_command_several_authors(
        self,
        jwt_user: JWTUser,
        variant_study_service: VariantStudyService,
        root_study_id: str,
    ):
        """
        Test two different users that are authors on two different commands of the same variant
        Set up:
            Retrieve the user that will be the owner of the study and variant
            Create a second user
            Create a study and a variant study
            Each user creates a command

        Tests:
            Test whether the commands have the `user_name` and `updated_at` attributes
            Test authors of the commands
        """
        # Get the owner request parameters

        # create another user that has the write privilege
        user2 = User(id=3, name="jane.doe", type="users")
        db.session.add(user2)
        db.session.commit()

        # Generate a variant on a study that allow other user to edit it
        variant_study = variant_study_service.create_variant_study(root_study_id, "new variant")
        study_version = StudyVersion.parse(variant_study.version)
        variant_id = variant_study.id

        # Create two new commands on the existing variant
        command_6 = CommandDTO(action="update_comments", args={"comments": "new comment"}, study_version=study_version)
        command_7 = CommandDTO(
            action="update_comments", args={"comments": "another new comment"}, study_version=study_version
        )

        variant_study_service.append_command(variant_id, command_6)
        variant_study_service.append_command(variant_id, command_7)

        # Make sure there are commands generated by both users
        commands = variant_study_service.get_commands(variant_id)
        assert len(commands) == 2

        # Make sure their `user_name` and `updated_at` attributes are not None
        for command in commands:
            assert command.user_name and command.updated_at

        # Make sure commands has not the same author
        assert commands[0] != commands[1]
        assert commands[0].user_name == "john.doe"
        assert commands[1].user_name == "jane.doe"

    @pytest.mark.parametrize("root_study_id", [False], indirect=True)
    @with_db_context
    def test_command_same_author(
        self,
        jwt_user: JWTUser,
        variant_study_service: VariantStudyService,
        root_study_id: str,
    ):
        """
        Test the case of multiple commands was created by the same user.
        Set up:
            Initialize a counter of queries to database
            Define a watcher on the orm queries to database that updates the counter
            Create a user
            Create a variant study
            Make the user generates five commands on the newly created variant
        Test:
            Each time a command is retrieved, the database must be accessed only if
            the author of the currently retrieved command is not already known during
            the process
        """
        nb_queries = 0  # Store number of orm queries to database

        # Watch orm events and update `nb_queries`
        @event.listens_for(db.session, "do_orm_execute")
        def check_orm_operations(orm_execute_state):
            if orm_execute_state.is_select:
                nonlocal nb_queries
                nb_queries += 1

        # Generate a variant on a study that allow other user to edit it
        variant_study = variant_study_service.create_variant_study(root_study_id, "new_variant")

        commands = []

        # Create two new commands on the existing variant
        for index in range(5):
            commands.append(
                CommandDTO(
                    action="update_comments",
                    args={"comments": f"new comment {index}"},
                    study_version=StudyVersion.parse(variant_study.version),
                )
            )
        variant_study_service.append_commands(variant_study.id, commands)

        nb_queries_before = nb_queries  # store initial state
        variant_study_service.get_commands(variant_study.id)  # execute database query
        assert nb_queries_before + 1 == nb_queries  # compare with initial state to make sure database was queried once
