import datetime
from pathlib import Path
from unittest.mock import Mock, ANY

from sqlalchemy import create_engine

from antarest.core.cache.business.local_chache import LocalCache
from antarest.core.config import Config, StorageConfig, WorkspaceConfig
from antarest.core.jwt import JWTUser, JWTGroup
from antarest.core.persistence import Base
from antarest.core.requests import RequestParameters
from antarest.core.roles import RoleType
from antarest.core.utils.fastapi_sqlalchemy import DBSessionMiddleware, db
from antarest.matrixstore.service import MatrixService
from antarest.study.model import (
    DEFAULT_WORKSPACE_NAME,
    RawStudy,
    StudyAdditionalData,
)
from antarest.study.storage.variantstudy.command_factory import CommandFactory
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy
from antarest.study.storage.variantstudy.model.model import (
    CommandDTO,
    GenerationResultInfoDTO,
)
from antarest.study.storage.variantstudy.repository import (
    VariantStudyRepository,
)
from antarest.study.storage.variantstudy.variant_study_service import (
    VariantStudyService,
    SNAPSHOT_RELATIVE_PATH,
)

SADMIN = RequestParameters(
    user=JWTUser(
        id=0,
        impersonator=0,
        type="users",
        groups=[JWTGroup(id="admin", name="admin", role=RoleType.ADMIN)],
    )
)


def test_commands_service(
    tmp_path: Path, command_factory: CommandFactory
) -> VariantStudyService:
    engine = create_engine(
        "sqlite:///:memory:",
        echo=True,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    DBSessionMiddleware(
        Mock(),
        custom_engine=engine,
        session_args={"autocommit": False, "autoflush": False},
    )
    repository = VariantStudyRepository(LocalCache())
    service = VariantStudyService(
        raw_study_service=Mock(),
        cache=Mock(),
        task_service=Mock(),
        command_factory=command_factory,
        study_factory=Mock(),
        config=Config(
            storage=StorageConfig(
                workspaces={
                    DEFAULT_WORKSPACE_NAME: WorkspaceConfig(path=tmp_path)
                }
            )
        ),
        repository=repository,
        event_bus=Mock(),
        patch_service=Mock(),
    )

    with db():
        # Save a study
        origin_id = "origin-id"
        origin_study = RawStudy(
            id=origin_id,
            name="my-study",
            additional_data=StudyAdditionalData(),
        )
        repository.save(origin_study)

        # Create un new variant
        name = "my-variant"
        saved_id = service.create_variant_study(origin_id, name, SADMIN)

        study = repository.get(saved_id)
        assert study.id == saved_id
        assert study.parent_id == origin_id

        # Append command
        command_1 = CommandDTO(action="create_area", args={"area_name": "Yes"})
        service.append_command(saved_id, command_1, SADMIN)
        command_2 = CommandDTO(action="create_area", args={"area_name": "No"})
        service.append_command(saved_id, command_2, SADMIN)
        commands = service.get_commands(saved_id, SADMIN)
        assert len(commands) == 2

        # Append multiple commands
        command_3 = CommandDTO(
            action="create_area", args={"area_name": "Maybe"}
        )
        command_4 = CommandDTO(
            action="create_link", args={"area1": "No", "area2": "Yes"}
        )
        service.append_commands(saved_id, [command_3, command_4], SADMIN)
        commands = service.get_commands(saved_id, SADMIN)
        assert len(commands) == 4

        # Get command
        assert commands[0] == service.get_command(
            saved_id, commands[0].id, SADMIN
        )

        # Remove command
        service.remove_command(saved_id, commands[2].id, SADMIN)
        commands = service.get_commands(saved_id, SADMIN)
        assert len(commands) == 3

        # Update command
        command_5 = CommandDTO(
            action="replace_matrix",
            args={"target": "some/matrix/path", "matrix": [[0]]},
        )
        service.update_command(
            study_id=saved_id,
            command_id=commands[2].id,
            command=command_5,
            params=SADMIN,
        )
        commands = service.get_commands(saved_id, SADMIN)
        assert commands[2].action == "replace_matrix"
        assert commands[2].args["matrix"] == "matrix_id"

        # Move command
        service.move_command(
            study_id=saved_id,
            command_id=commands[2].id,
            new_index=0,
            params=SADMIN,
        )
        commands = service.get_commands(saved_id, SADMIN)
        assert commands[0].action == "replace_matrix"

        # Generate
        service._generate_snapshot = Mock()
        service._read_additional_data_from_files = Mock()
        service._read_additional_data_from_files.return_value = (
            StudyAdditionalData()
        )
        expected_result = GenerationResultInfoDTO(success=True, details=[])
        service._generate_snapshot.return_value = expected_result
        results = service._generate(saved_id, SADMIN, False)
        assert results == expected_result
        assert study.snapshot.id == study.id


def test_smart_generation(
    tmp_path: Path, command_factory: CommandFactory
) -> None:
    engine = create_engine(
        "sqlite:///:memory:",
        echo=True,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    DBSessionMiddleware(
        Mock(),
        custom_engine=engine,
        session_args={"autocommit": False, "autoflush": False},
    )
    repository = VariantStudyRepository(LocalCache())
    service = VariantStudyService(
        raw_study_service=Mock(),
        cache=Mock(),
        task_service=Mock(),
        command_factory=command_factory,
        study_factory=Mock(),
        config=Config(
            storage=StorageConfig(
                workspaces={
                    DEFAULT_WORKSPACE_NAME: WorkspaceConfig(path=tmp_path)
                }
            )
        ),
        repository=repository,
        event_bus=Mock(),
        patch_service=Mock(),
    )
    service.generator = Mock()
    service.generator.generate.side_effect = [
        GenerationResultInfoDTO(success=True, details=[]),
        GenerationResultInfoDTO(success=True, details=[]),
        GenerationResultInfoDTO(success=True, details=[]),
        GenerationResultInfoDTO(success=True, details=[]),
    ]

    def export_flat(
        metadata: VariantStudy,
        dest: Path,
        outputs: bool = True,
        denormalize: bool = True,
    ) -> None:
        dest.mkdir(parents=True)
        (dest / "user").mkdir()
        (dest / "user" / "some_unmanaged_config").touch()

    service.raw_study_service.export_study_flat.side_effect = export_flat

    with db():
        origin_id = "base-study"
        origin_study = RawStudy(
            id=origin_id,
            name="my-study",
            workspace=DEFAULT_WORKSPACE_NAME,
            additional_data=StudyAdditionalData(),
            updated_at=datetime.datetime(year=2000, month=1, day=1),
        )
        repository.save(origin_study)

        variant_id = service.create_variant_study(
            origin_id, "my variant", SADMIN
        )
        unmanaged_user_config_path = (
            tmp_path
            / variant_id
            / SNAPSHOT_RELATIVE_PATH
            / "user"
            / "some_unmanaged_config"
        )
        assert not unmanaged_user_config_path.exists()

        service.append_command(
            variant_id,
            CommandDTO(action="create_area", args={"area_name": "a"}),
            SADMIN,
        )
        service._read_additional_data_from_files = Mock()
        service._read_additional_data_from_files.return_value = (
            StudyAdditionalData()
        )
        service._generate(variant_id, SADMIN, False)
        service.generator.generate.assert_called_with(
            [ANY], ANY, ANY, notifier=ANY
        )

        service._generate(variant_id, SADMIN, False)
        service.generator.generate.assert_called_with(
            [], ANY, ANY, notifier=ANY
        )

        service.append_command(
            variant_id,
            CommandDTO(action="create_area", args={"area_name": "b"}),
            SADMIN,
        )
        assert (
            service._get_variant_study(
                variant_id, SADMIN
            ).snapshot.last_executed_command
            is not None
        )
        service._generate(variant_id, SADMIN, False)
        service.generator.generate.assert_called_with(
            [ANY], ANY, ANY, notifier=ANY
        )

        service.replace_commands(
            variant_id,
            [
                CommandDTO(action="create_area", args={"area_name": "c"}),
                CommandDTO(action="create_area", args={"area_name": "d"}),
            ],
            SADMIN,
        )

        assert unmanaged_user_config_path.exists()
        unmanaged_user_config_path.write_text("hello")
        service._generate(variant_id, SADMIN, False)
        service.generator.generate.assert_called_with(
            [ANY, ANY], ANY, ANY, notifier=ANY
        )
        assert unmanaged_user_config_path.read_text() == "hello"
