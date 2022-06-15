from typing import Union, List, Any, Tuple, Dict

from pydantic import validator

from antarest.core.model import JSON
from antarest.core.utils.utils import assert_this
from antarest.matrixstore.model import MatrixData
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    ChildNotFoundError,
)
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import (
    MatrixNode,
)
from antarest.study.storage.variantstudy.business.utils import (
    validate_matrix,
    strip_matrix_protocol,
    AliasDecoder,
)
from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.icommand import (
    ICommand,
    MATCH_SIGNATURE_SEPARATOR,
)
from antarest.study.storage.variantstudy.model.model import CommandDTO


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

    def _apply_config(
        self, study_data: FileStudyTreeConfig
    ) -> Tuple[CommandOutput, Dict[str, Any]]:
        return (
            CommandOutput(
                status=True,
                message=f"Matrix '{self.target}' has been successfully replaced.",
            ),
            dict(),
        )

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        if self.target[0] == "@":
            self.target = AliasDecoder.decode(self.target, study_data)

        replace_matrix_data: JSON = {}
        target_matrix = replace_matrix_data
        url = self.target.split("/")
        for element in url[:-1]:
            target_matrix[element] = {}
            target_matrix = target_matrix[element]

        target_matrix[url[-1]] = self.matrix

        try:
            last_node = study_data.tree.get_node(url)
            assert_this(isinstance(last_node, MatrixNode))
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
        output, _ = self._apply_config(study_data.config)
        return output

    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.REPLACE_MATRIX.value,
            args={
                "target": self.target,
                "matrix": strip_matrix_protocol(self.matrix),
            },
        )

    def match_signature(self) -> str:
        return str(
            self.command_name.value + MATCH_SIGNATURE_SEPARATOR + self.target
        )

    def match(self, other: ICommand, equal: bool = False) -> bool:
        if not isinstance(other, ReplaceMatrix):
            return False
        simple_match = self.target == other.target
        if not equal:
            return simple_match
        return simple_match and self.matrix == other.matrix

    def _create_diff(self, other: "ICommand") -> List["ICommand"]:
        return [other]

    def get_inner_matrices(self) -> List[str]:
        assert_this(isinstance(self.matrix, str))
        return [strip_matrix_protocol(self.matrix)]
