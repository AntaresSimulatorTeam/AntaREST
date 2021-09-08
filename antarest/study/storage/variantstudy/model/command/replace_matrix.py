from typing import Union, List, Any

from pydantic import validator

from antarest.core.custom_types import JSON
from antarest.matrixstore.model import MatrixContent
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand


class ReplaceMatrix(ICommand):
    target_element: str
    matrix: Union[List[List[float]], str]

    @validator("matrix", each_item=True, always=True)
    def validate_matrix(
        cls, v: Union[List[List[float]], str], values: Any
    ) -> Union[List[List[float]], str]:
        if isinstance(v, list):
            v = "matrix://" + values["command_context"].matrix_service.create(
                data=MatrixContent(data=v)
            )
        elif isinstance(v, str):
            if values["command_context"].matrix_service.get(v):
                v = "matrix://" + v
            else:
                raise ValueError(f"Matrix with id {v} does not exist")
        else:
            raise ValueError(
                f"The data {v} is neither a matrix nor a link to a matrix"
            )

        return v

    def __init__(self, **data: Any) -> None:
        super().__init__(
            command_name=CommandName.REPLACE_MATRIX, version=1, **data
        )

    def apply(self, study_data: FileStudy) -> CommandOutput:
        replace_matrix_data: JSON = {}
        target_matrix = replace_matrix_data
        url = self.target_element.split("/")
        for element in url[:-1]:
            target_matrix[element] = {}
            target_matrix = target_matrix[element]

        target_matrix[url[-1]] = self.matrix

        try:
            study_data.tree.save(replace_matrix_data)
        except KeyError:
            return CommandOutput(
                status=False,
                message=f"Path '{self.target_element}' does not exist or does not target a matrix.",
            )

        return CommandOutput(
            status=True,
            message=f"Matrix '{self.target_element}' has been successfully replaced.",
        )

    def revert(self, study_data: FileStudy) -> CommandOutput:
        raise NotImplementedError()
