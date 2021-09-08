from pathlib import Path
from unittest.mock import Mock

from sqlalchemy import create_engine

from antarest.core.config import Config, StorageConfig, WorkspaceConfig
from antarest.core.jwt import JWTUser, JWTGroup
from antarest.core.persistence import Base
from antarest.core.requests import RequestParameters
from antarest.core.roles import RoleType
from antarest.core.utils.fastapi_sqlalchemy import DBSessionMiddleware, db
from antarest.study.model import DEFAULT_WORKSPACE_NAME, RawStudy
from antarest.study.storage.variantstudy.model import (
    CommandDTO,
    GenerationResultInfoDTO,
)
from antarest.study.storage.variantstudy.repository import (
    VariantStudyRepository,
)
from antarest.study.storage.variantstudy.variant_study_service import (
    VariantStudyService,
)

SADMIN = RequestParameters(
    user=JWTUser(
        id=0,
        impersonator=0,
        type="users",
        groups=[JWTGroup(id="admin", name="admin", role=RoleType.ADMIN)],
    )
)


def test_service() -> VariantStudyService:
    engine = create_engine("sqlite:///:memory:", echo=True)
    Base.metadata.create_all(engine)
    DBSessionMiddleware(
        Mock(),
        custom_engine=engine,
        session_args={"autocommit": False, "autoflush": False},
    )
    repository = VariantStudyRepository()
    service = VariantStudyService(
        raw_study_service=Mock(),
        command_factory=Mock(),
        study_factory=Mock(),
        exporter_service=Mock(),
        config=Config(
            storage=StorageConfig(
                workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig()}
            )
        ),
        repository=repository,
        event_bus=Mock(),
        patch_service=Mock(),
    )

    with db():
        # Save a study
        origin_id = "origin-id"
        origin_study = RawStudy(id=origin_id, name="my-study")
        repository.save(origin_study)

        # Create un new variant
        name = "my-variant"
        saved_id = service.create_variant_study(origin_id, name, SADMIN)

        study = repository.get(saved_id)
        assert study.id == saved_id
        assert study.parent_id == origin_id

        # Append command
        command_1 = CommandDTO(action="My-action-1", args={"arg_1": "Yes"})
        service.append_command(saved_id, command_1, SADMIN)
        command_2 = CommandDTO(action="My-action-2", args={"arg_2": "No"})
        service.append_command(saved_id, command_2, SADMIN)
        commands = service.get_commands(saved_id, SADMIN)
        assert len(commands) == 2

        # Append multiple commands
        command_3 = CommandDTO(action="My-action-3", args={"arg_3": "No"})
        command_4 = CommandDTO(action="My-action-4", args={"arg_4": "No"})
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
        command_5 = CommandDTO(action="My-action-5", args={"arg_5": "No"})
        service.update_command(
            study_id=saved_id,
            command_id=commands[2].id,
            command=command_5,
            params=SADMIN,
        )
        commands = service.get_commands(saved_id, SADMIN)
        assert commands[2].action == "My-action-5"

        # Move command
        service.move_command(
            study_id=saved_id,
            command_id=commands[2].id,
            new_index=0,
            params=SADMIN,
        )
        commands = service.get_commands(saved_id, SADMIN)
        assert commands[0].action == "My-action-5"

        # Generate
        service.generator.generate_snapshot = Mock()
        expected_result = GenerationResultInfoDTO(success=True, details=[])
        service.generator.generate_snapshot.return_value = expected_result
        results = service.generate(saved_id, False, SADMIN)
        assert results == expected_result
        assert study.snapshot.id == study.id
        assert study.snapshot.path == str(Path(study.path) / "snapshot")
