from typing import Union, List, Any

from pydantic import validator

from antarest.core.custom_types import JSON
from antarest.matrixstore.model import MatrixContent, MatrixData
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    ChildNotFoundError,
)
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import (
    MatrixNode,
)
from antarest.study.storage.variantstudy.model.model import CommandDTO
from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.utils import (
    validate_matrix,
    strip_matrix_protocol,
)


class ReplaceMatrix(ICommand):
    target: str
    matrix: Union[List[List[MatrixData]], str]

    _validate_matrix = validator(
        "matrix", each_item=True, always=True, allow_reuse=True
    )(validate_matrix)

    def __init__(self, **data: Any) -> None:
        super().__init__(
            command_name=CommandName.REPLACE_MATRIX, version=1, **data
        )

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        replace_matrix_data: JSON = {}
        target_matrix = replace_matrix_data
        url = self.target.split("/")
        for element in url[:-1]:
            target_matrix[element] = {}
            target_matrix = target_matrix[element]

        target_matrix[url[-1]] = self.matrix

        try:
            last_node = study_data.tree.get_node(url)
            assert isinstance(last_node, MatrixNode)
        except (KeyError, ChildNotFoundError):
            return CommandOutput(
                status=False,
                message=f"Path '{self.target}' does not exist.",
            )
        except AssertionError:
            return CommandOutput(
                status=False,
                message=f"Path '{self.target}' does not target a matrix.",
            )

        study_data.tree.save(replace_matrix_data)

        return CommandOutput(
            status=True,
            message=f"Matrix '{self.target}' has been successfully replaced.",
        )

    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.REPLACE_MATRIX.value,
            args={
                "target": self.target,
                "matrix": strip_matrix_protocol(self.matrix),
            },
        )
