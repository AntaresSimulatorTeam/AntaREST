from typing import Union, List, Any

from antarest.core.custom_types import JSON
from antarest.matrixstore.model import MatrixContent
from antarest.study.storage.variantstudy.business.matrix_constants_generator import (
    MATRIX_PROTOCOL_PREFIX,
)
from antarest.study.storage.variantstudy.model.model import CommandDTO


def validate_matrix(matrix: Union[List[List[float]], str], values: Any) -> str:
    matrix_id: str
    if isinstance(matrix, list):
        matrix_id = MATRIX_PROTOCOL_PREFIX + values[
            "command_context"
        ].matrix_service.create(data=MatrixContent(data=matrix))
    elif isinstance(matrix, str):
        if values["command_context"].matrix_service.get(matrix):
            matrix_id = MATRIX_PROTOCOL_PREFIX + matrix
        else:
            raise ValueError(f"Matrix with id {matrix} does not exist")
    else:
        raise ValueError(
            f"The data {matrix} is neither a matrix nor a link to a matrix"
        )

    return matrix_id


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
