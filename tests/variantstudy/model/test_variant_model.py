# Copyright (c) 2026, RTE (https://www.rte-france.com)
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

from antarest.core.jwt import JWTGroup, JWTUser
from antarest.core.model import PublicMode
from antarest.core.roles import RoleType
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.login.model import Group, Role, User
from antarest.login.utils import current_user_context, get_current_user
from antarest.study.dao.database.database_study_factory_dao import DatabaseStudyDaoFactory
from antarest.study.dao.file.file_study_dao import FileStudyTreeDao
from antarest.study.dao.file.file_study_factory_dao import FileStudyDaoFactory
from antarest.study.model import STUDY_VERSION_8_6, StorageMode, StudyMetadataCreation
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.utils import create_new_empty_study
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy
from antarest.study.storage.variantstudy.model.model import CommandDTO, CommandDTOAPI
from antarest.study.storage.variantstudy.snapshot.snapshot_generator import SnapshotGenerator
from antarest.study.storage.variantstudy.variant_study_service import VariantStudyService
from tests.db_statement_recorder import DBStatementRecorder
from tests.helpers import create_raw_study, with_admin_user, with_db_context


def create_root_study(
    public_mode: PublicMode,
    tmp_path: Path,
    variant_study_service: VariantStudyService,
    user_id: int,
    storage_mode: StorageMode = StorageMode.FILESYSTEM,
) -> str:
    # Prepare a RAW study in the temporary folder
    study_dir = tmp_path / "my_study"
    root_study_id = str(uuid.uuid4())
    root_study = create_raw_study(
        id=root_study_id,
        workspace="default",
        path=str(study_dir),
        version="860",
        created_at=datetime.datetime.now(datetime.UTC).replace(tzinfo=None),
        updated_at=datetime.datetime.now(datetime.UTC).replace(tzinfo=None),
        author="john.doe",
        owner_id=user_id,
        public_mode=public_mode,
        storage_mode=storage_mode,
    )
    if storage_mode == StorageMode.FILESYSTEM:
        # Saves the study on disk
        create_new_empty_study(STUDY_VERSION_8_6, study_dir, author="john.doe")
    with db():
        # Save the root study in database
        variant_study_service.repository.save(root_study)
        if storage_mode == StorageMode.DATABASE:
            # Initialize the study data
            ctx = variant_study_service.command_factory.command_context
            factory = DatabaseStudyDaoFactory(ctx.matrix_service, ctx.generator_matrix_constants)
            metadata = StudyMetadataCreation(id=root_study_id, name="my_study", version=STUDY_VERSION_8_6, managed=True)
            factory.create_study_dao(metadata)
    return root_study_id


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
        fs_dao: FileStudyTreeDao,
        raw_study_service: RawStudyService,
        variant_study_service: VariantStudyService,
        jwt_user: JWTUser,
        request: t.Any,
    ) -> str:
        # Get public mode argument
        public_mode = request.param
        return create_root_study(public_mode, tmp_path, variant_study_service, jwt_user.id)

    @with_admin_user
    @with_db_context
    @pytest.mark.parametrize("storage_mode", [StorageMode.FILESYSTEM, StorageMode.DATABASE])
    def test_commands_service(
        self, variant_study_service: VariantStudyService, tmp_path: Path, storage_mode: StorageMode
    ) -> None:
        jwt_user = get_current_user()
        root_study_id = create_root_study(PublicMode.NONE, tmp_path, variant_study_service, jwt_user.id, storage_mode)
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
        variant_study_service.append_commands(saved_id, [command_1])
        command_count += 1

        command_2 = CommandDTO(action="create_area", args={"area_name": "No"}, study_version=study_version)
        variant_study_service.append_commands(saved_id, [command_2])
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
            variant_study_service.get_commands(saved_id)[0].model_dump(mode="json", exclude={"study_version"})
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
        variant_study_service.append_commands(saved_id, [command_5])
        command_count += 1

        commands = variant_study_service.get_commands(saved_id)
        assert len(commands) == command_count

        # Generate using the SnapshotGenerator
        generator = SnapshotGenerator(variant_study_service)
        # Build the dao factory
        ctx = variant_study_service.command_factory.command_context

        if variant_study.storage_mode == StorageMode.FILESYSTEM:
            factory = FileStudyDaoFactory(
                ctx.matrix_service,
                ctx.blob_service,
                ctx.generator_matrix_constants,
                variant_study_service.study_factory,
                variant_study_service.cache,
                variant_study_service.get_study_paths,
            )
        else:
            factory = DatabaseStudyDaoFactory(ctx.matrix_service, ctx.generator_matrix_constants)
        # Generate the snapshot
        results = generator.generate_snapshot(saved_id, dao_factory=factory)
        # Check the results. `details` should be empty as all commands were applied synchronously
        assert results.model_dump() == {"success": True, "should_invalidate_cache": False, "details": []}
        assert study.snapshot.id == study.id

    @with_db_context
    def test_command_several_authors(
        self, jwt_user: JWTUser, variant_study_service: VariantStudyService, tmp_path: Path
    ) -> None:
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
        root_study_id = create_root_study(PublicMode.EDIT, tmp_path, variant_study_service, jwt_user.id)

        # create another user that has the write privilege
        other_user = User(id=3, name="jane.doe", type="users")
        db.session.add(other_user)
        db.session.commit()
        user2 = JWTUser(
            id=other_user.id,
            impersonator=other_user.id,
            type="users",
            groups=[JWTGroup(id="writers", name="writers", role=RoleType.WRITER)],
        )

        # Generate a variant on a study that allow other user to edit it
        with current_user_context(jwt_user):
            variant_study = variant_study_service.create_variant_study(root_study_id, "new variant")
        study_version = StudyVersion.parse(variant_study.version)
        variant_id = variant_study.id

        # Create two new commands on the existing variant
        command_6 = CommandDTO(action="update_comments", args={"comments": "new comment"}, study_version=study_version)
        command_7 = CommandDTO(
            action="update_comments", args={"comments": "another new comment"}, study_version=study_version
        )

        with current_user_context(jwt_user):
            variant_study_service.append_commands(variant_id, [command_6])

        with current_user_context(user2):
            variant_study_service.append_commands(variant_id, [command_7])

        # Make sure there are commands generated by both users
        with current_user_context(jwt_user):
            commands = variant_study_service.get_commands(variant_id)
        assert len(commands) == 2

        # Make sure their `user_name` and `updated_at` attributes are not None
        for command in commands:
            assert command.user_name and command.updated_at

        # Make sure commands has not the same author
        assert commands[0] != commands[1]
        assert commands[0].user_name == "john.doe"
        assert commands[1].user_name == "jane.doe"

    @with_db_context
    def test_command_same_author(
        self, jwt_user: JWTUser, variant_study_service: VariantStudyService, tmp_path: Path
    ) -> None:
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
        # Generate a variant on a study that allow other user to edit it
        root_study_id = create_root_study(PublicMode.NONE, tmp_path, variant_study_service, jwt_user.id)
        with current_user_context(jwt_user):
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
        with current_user_context(jwt_user):
            variant_study_service.append_commands(variant_study.id, commands)

        with current_user_context(jwt_user):
            with DBStatementRecorder(db.session.bind) as db_recorder:
                variant_study_service.get_commands(variant_study.id)
                # Only 1 query must be executed:
                # 1. Get the variant study with its owner, groups and commands
                # 2. Retrieves the user's name. Performed only once as the same user added the 5 commands (no N+1 query)
                assert len(db_recorder.sql_statements) == 1

    @with_admin_user
    @with_db_context
    def test_update_editor(self, jwt_user: JWTUser, variant_study_service: VariantStudyService, tmp_path: Path) -> None:
        """
        Test two different users, one that is the author and the other that is an editor on one study of the service
        Set up:
            Retrieve the user that will be the owner of the study and variant
            Create a second user that will be the editor
            Create a variant study

        Tests:
        """
        root_study_id = create_root_study(PublicMode.NONE, tmp_path, variant_study_service, jwt_user.id)
        admin_group = JWTGroup(id="admin", name="admin", role=RoleType.ADMIN)
        test_user_editor = User(id=2, name="jane.editor", type="users")
        jwt_user_editor = JWTUser(
            id=test_user_editor.id, impersonator=test_user_editor.id, type="users", groups=[admin_group]
        )
        db.session.add(test_user_editor)
        db.session.commit()

        with current_user_context(jwt_user):
            variant_study = variant_study_service.create_variant_study(root_study_id, "new_variant_1")
        study_version = StudyVersion.parse(variant_study.version)
        saved_id = variant_study.id
        study = variant_study_service.repository.get(saved_id)
        assert study is not None
        assert study.id == saved_id
        assert study.parent_id == root_study_id
        assert study.author == "john.doe"
        assert study.editor == "john.doe"  # editor is the user who created the study

        # creating area by the author, making him the editor of the study
        command_1 = CommandDTO(action="create_area", args={"area_name": "area_be"}, study_version=study_version)
        command_2 = CommandDTO(action="create_area", args={"area_name": "area_fr"}, study_version=study_version)

        with current_user_context(jwt_user):
            variant_study_service.append_commands(variant_study.id, [command_1, command_2])

        study = variant_study_service.repository.get(saved_id)
        assert study.author == "john.doe"
        assert study.editor == "john.doe"
        # end creating area

        # creating a link between two areas with another user, making him the editor
        command_3 = CommandDTO(
            action="create_link", args={"area1": "area_be", "area2": "area_fr"}, study_version=study_version
        )

        with current_user_context(jwt_user_editor):
            variant_study_service.append_commands(variant_study.id, [command_3])

        study_db = db.session.get(VariantStudy, variant_study.id)
        assert study_db.author == "john.doe"
        assert study_db.editor == "jane.editor"
        # end creating link

        # deleting an area with the author, making him the editor, again
        command_4 = CommandDTO(action="remove_area", args={"id": "area_fr"}, study_version=study_version)

        with current_user_context(jwt_user):
            variant_study_service.append_commands(variant_study.id, [command_4])

        study_db = db.session.get(VariantStudy, variant_study.id)
        assert study_db.author == "john.doe"
        assert study_db.editor == "john.doe"
        # end deleting area
