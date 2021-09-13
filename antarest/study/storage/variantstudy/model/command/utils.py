from typing import Union, List, Any

from antarest.core.custom_types import JSON
from antarest.matrixstore.model import MatrixContent


def validate_matrix(
    matrix: Union[List[List[float]], str], values: Any
) -> Union[List[List[float]], str]:
    if isinstance(matrix, list):
        matrix = "matrix://" + values["command_context"].matrix_service.create(
            data=MatrixContent(data=matrix)
        )
    elif isinstance(matrix, str):
        if values["command_context"].matrix_service.get(matrix):
            matrix = "matrix://" + matrix
        else:
            raise ValueError(f"Matrix with id {matrix} does not exist")
    else:
        raise ValueError(
            f"The data {matrix} is neither a matrix nor a link to a matrix"
        )

    return matrix


def get_or_create_section(json_ini: JSON, section: str) -> JSON:
    if section not in json_ini:
        json_ini[section] = {}
    sub_json: JSON = json_ini[section]
    return sub_json
