import datetime
from unittest.mock import Mock

from sqlalchemy import create_engine

from antarest.core.config import Config, StorageConfig, WorkspaceConfig
from antarest.core.jwt import JWTUser, JWTGroup
from antarest.core.persistence import Base
from antarest.core.requests import RequestParameters
from antarest.core.roles import RoleType
from antarest.core.utils.fastapi_sqlalchemy import DBSessionMiddleware, db
from antarest.study.model import Study, DEFAULT_WORKSPACE_NAME
from antarest.study.repository import StudyMetadataRepository
from antarest.study.storage.variantstudy.model import CommandDTO
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
    repository = StudyMetadataRepository()
    service = VariantStudyService(
        config=Config(
            storage=StorageConfig(
                workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig()}
            )
        ),
        repository=repository,
        event_bus=Mock(),
    )
    with db():
        # Save a study
        origin_id = "origin-id"
        origin_study = Study(id=origin_id, name="my-study")
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
        command_3 = CommandDTO(action="My-action-3", args={"arg_3": "No"})
        service.append_command(saved_id, command_3, SADMIN)
        command_4 = CommandDTO(action="My-action-4", args={"arg_4": "No"})
        service.append_command(saved_id, command_4, SADMIN)
        assert len(study.commands) == 4

        commands = service.get_commands(saved_id, SADMIN)
        assert len(commands) == 4

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
