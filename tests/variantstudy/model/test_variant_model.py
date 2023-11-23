import datetime
import uuid
from pathlib import Path

import pytest

from antarest.core.jwt import JWTGroup, JWTUser
from antarest.core.requests import RequestParameters
from antarest.core.roles import RoleType
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.login.model import Group, Role, User
from antarest.study.model import RawStudy, StudyAdditionalData
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from antarest.study.storage.variantstudy.model.model import CommandDTO, GenerationResultInfoDTO
from antarest.study.storage.variantstudy.snapshot_generator import SnapshotGenerator
from antarest.study.storage.variantstudy.variant_study_service import VariantStudyService
from tests.helpers import with_db_context


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
    ) -> str:
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
        )
        root_study = raw_study_service.create(root_study)
        with db():
            # Save the root study in database
            variant_study_service.repository.save(root_study)
        return root_study_id

    @with_db_context
    def test_commands_service(
        self,
        root_study_id: str,
        generator_matrix_constants: GeneratorMatrixConstants,
        jwt_user: JWTUser,
        variant_study_service: VariantStudyService,
    ) -> None:
        # Initialize the default matrix constants
        # noinspection PyProtectedMember
        generator_matrix_constants.init_constant_matrices()

        params = RequestParameters(user=jwt_user)

        # Create un new variant
        variant_study = variant_study_service.create_variant_study(root_study_id, "my-variant", params=params)
        saved_id = variant_study.id
        study = variant_study_service.repository.get(saved_id)
        assert study is not None
        assert study.id == saved_id
        assert study.parent_id == root_study_id

        # Append command
        command_count = 0
        command_1 = CommandDTO(action="create_area", args={"area_name": "Yes"})
        variant_study_service.append_command(saved_id, command_1, params=params)
        command_count += 1

        command_2 = CommandDTO(action="create_area", args={"area_name": "No"})
        variant_study_service.append_command(saved_id, command_2, params=params)
        command_count += 1

        commands = variant_study_service.get_commands(saved_id, params=params)
        assert len(commands) == command_count

        # Append multiple commands
        command_3 = CommandDTO(action="create_area", args={"area_name": "Maybe"})
        command_4 = CommandDTO(action="create_link", args={"area1": "no", "area2": "yes"})
        variant_study_service.append_commands(saved_id, [command_3, command_4], params=params)
        command_count += 2

        commands = variant_study_service.get_commands(saved_id, params=params)
        assert len(commands) == command_count

        # Get command
        assert commands[0] == variant_study_service.get_command(saved_id, commands[0].id, params=params)

        # Remove command (area "Maybe")
        variant_study_service.remove_command(saved_id, commands[2].id, params=params)
        command_count -= 1

        # Create a thermal cluster in the area "Yes"
        command_5 = CommandDTO(
            action="create_cluster",
            args={
                "area_id": "yes",
                "cluster_name": "cl1",
                "parameters": {"group": "Gas", "unitcount": 1, "nominalcapacity": 500},
            },
        )
        variant_study_service.append_command(saved_id, command_5, params=params)
        command_count += 1

        commands = variant_study_service.get_commands(saved_id, params=params)
        assert len(commands) == command_count

        # Generate using the SnapshotGenerator
        generator = SnapshotGenerator(
            cache=variant_study_service.cache,
            raw_study_service=variant_study_service.raw_study_service,
            command_factory=variant_study_service.command_factory,
            study_factory=variant_study_service.study_factory,
            patch_service=variant_study_service.patch_service,
            repository=variant_study_service.repository,
        )
        results = generator.generate_snapshot(saved_id, jwt_user, denormalize=False)
        assert results == GenerationResultInfoDTO(
            success=True,
            details=[
                ("create_area", True, "Area 'Yes' created"),
                ("create_area", True, "Area 'No' created"),
                ("create_link", True, "Link between 'no' and 'yes' created"),
                ("create_cluster", True, "Thermal cluster 'cl1' added to area 'yes'."),
            ],
        )
        assert study.snapshot.id == study.id
