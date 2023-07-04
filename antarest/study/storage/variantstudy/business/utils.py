from typing import Any, Dict, List, Optional, Sequence, Union

from antarest.core.model import JSON
from antarest.matrixstore.model import MatrixData
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.matrix_constants_generator import (
    MATRIX_PROTOCOL_PREFIX,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.model import CommandDTO


def validate_matrix(
    matrix: Union[List[List[MatrixData]], str], values: Dict[str, Any]
) -> str:
    """
    Validates the matrix, stores the matrix array in the matrices repository,
    and returns a reference to the stored array.

    Args:
        matrix: The matrix data or matrix link to validate.
        values: Additional values used during the validation process.
            It should contain the following key-value pairs:
            - "command_context": An object providing access to matrix services.
              It should have a "matrix_service" attribute which allows creating
              and checking the existence of matrices.

    Returns:
        The ID of the validated matrix prefixed by "matrix://".

    Raises:
        TypeError: If the provided matrix is neither a matrix nor a link to a matrix.
        ValueError: If the matrix ID does not exist.
    """
    # fmt: off
    matrix_service: ISimpleMatrixService = values["command_context"].matrix_service
    if isinstance(matrix, list):
        return MATRIX_PROTOCOL_PREFIX + matrix_service.create(data=matrix)
    elif isinstance(matrix, str):
        if matrix_service.exists(matrix):
            return MATRIX_PROTOCOL_PREFIX + matrix
        else:
            raise ValueError(f"Matrix with id {matrix} does not exist")
    else:
        raise TypeError(f"The data {matrix} is neither a matrix nor a link to a matrix")
    # fmt: on


def get_or_create_section(json_ini: JSON, section: str) -> JSON:
    if section not in json_ini:
        json_ini[section] = {}
    sub_json: JSON = json_ini[section]
    return sub_json


def remove_none_args(command_dto: CommandDTO) -> CommandDTO:
    if isinstance(command_dto.args, list):
        command_dto.args = [
            {k: v for k, v in args.items() if v is not None}
            for args in command_dto.args
        ]
    else:
        command_dto.args = {
            k: v for k, v in command_dto.args.items() if v is not None
        }
    return command_dto


def strip_matrix_protocol(
    matrix_uri: Union[List[List[float]], str, None]
) -> str:
    assert isinstance(matrix_uri, str)
    if matrix_uri.startswith(MATRIX_PROTOCOL_PREFIX):
        return matrix_uri[len(MATRIX_PROTOCOL_PREFIX) :]
    return matrix_uri


class AliasDecoder:
    @staticmethod
    def links_series(alias: str, study: FileStudy) -> str:
        data = alias.split("/")
        area_from = data[1]
        area_to = data[2]
        if study.config.version < 820:
            return f"input/links/{area_from}/{area_to}"
        return f"input/links/{area_from}/{area_to}_parameters"

    @staticmethod
    def decode(alias: str, study: FileStudy) -> str:
        alias_map = {"@links_series": AliasDecoder.links_series}
        alias_code = alias.split("/")[0]
        if alias_code in alias_map:
            return alias_map[alias_code](alias, study)
        raise NotImplementedError(f"Alias {alias} not implemented")


def transform_command_to_dto(
    commands: Sequence[ICommand],
    ref_commands: Optional[Sequence[CommandDTO]] = None,
    force_aggregate: bool = False,
) -> List[CommandDTO]:
    if len(commands) <= 1:
        return [command.to_dto() for command in commands]
    commands_dto: List[CommandDTO] = []
    ref_commands_dto = (
        ref_commands
        if ref_commands is not None
        else [command.to_dto() for command in commands]
    )
    prev_command = commands[0]
    cur_dto_index = 0
    cur_dto = ref_commands_dto[cur_dto_index]
    cur_dto_arg_count = (
        1 if isinstance(cur_dto.args, dict) else len(cur_dto.args)
    )
    cur_command_args_batch = [prev_command.to_dto().args]
    for command in commands[1:]:
        cur_dto_arg_count -= 1
        if command.command_name == prev_command.command_name and (
            cur_dto_arg_count > 0 or force_aggregate
        ):
            cur_command_args_batch.append(command.to_dto().args)
        else:
            commands_dto.append(
                CommandDTO(
                    action=prev_command.command_name.value,
                    args=cur_command_args_batch,
                )
            )
            cur_command_args_batch = [command.to_dto().args]
            cur_dto_index += 1
            cur_dto = ref_commands_dto[cur_dto_index]
            cur_dto_arg_count = (
                1 if isinstance(cur_dto.args, dict) else len(cur_dto.args)
            )
            prev_command = command
    commands_dto.append(
        CommandDTO(
            action=prev_command.command_name.value, args=cur_command_args_batch
        )
    )
    return commands_dto
