from typing import List, Sequence

from antarest.core.exceptions import CommandApplicationError
from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.requests import RequestParameters
from antarest.study.model import Study, RawStudy
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.utils import remove_from_cache
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.model import CommandDTO


def execute_or_add_commands(
    study: Study,
    file_study: FileStudy,
    commands: Sequence[ICommand],
    storage_service: StudyStorageService,
) -> None:
    if isinstance(study, RawStudy):
        executed_commands: List[ICommand] = []
        for command in commands:
            result = command.apply(file_study)
            if not result.status:
                raise CommandApplicationError(result.message)
            executed_commands.append(command)
        remove_from_cache(storage_service.raw_study_service.cache, study.id)
    else:
        storage_service.variant_study_service.append_commands(
            study.id,
            aggregate_commands(commands),
            RequestParameters(user=DEFAULT_ADMIN_USER),
        )


def aggregate_commands(commands: Sequence[ICommand]) -> List[CommandDTO]:
    if len(commands) <= 1:
        return [command.to_dto() for command in commands]
    commands_dto: List[CommandDTO] = []
    prev_command = commands[0]
    cur_command_args_batch = [prev_command.to_dto().args]
    for command in commands[1:]:
        if command.command_name == prev_command.command_name:
            cur_command_args_batch.append(command.to_dto().args)
        else:
            commands_dto.append(
                CommandDTO(
                    action=prev_command.command_name.value,
                    args=cur_command_args_batch,
                )
            )
            cur_command_args_batch = [command.to_dto().args]
        prev_command = command
    commands_dto.append(
        CommandDTO(
            action=prev_command.command_name.value, args=cur_command_args_batch
        )
    )
    return commands_dto
