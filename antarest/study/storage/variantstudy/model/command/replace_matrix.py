import typing as t

from pydantic import Field, ValidationInfo, field_validator

from antarest.core.exceptions import ChildNotFoundError
from antarest.core.model import JSON
from antarest.core.utils.utils import assert_this
from antarest.matrixstore.model import MatrixData
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixNode
from antarest.study.storage.variantstudy.business.utils import AliasDecoder, strip_matrix_protocol, validate_matrix
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import MATCH_SIGNATURE_SEPARATOR, ICommand
from antarest.study.storage.variantstudy.model.model import CommandDTO


class ReplaceMatrix(ICommand):
    """
    Command used to replace a matrice in an area.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.REPLACE_MATRIX
    version: int = 1

    # Command parameters
    # ==================

    target: str
    matrix: t.Union[t.List[t.List[MatrixData]], str] = Field(validate_default=True)

    @field_validator("matrix", mode="before")
    def matrix_validator(cls, matrix: t.Union[t.List[t.List[MatrixData]], str], values: ValidationInfo) -> str:
        return validate_matrix(matrix, values.data)

    def _apply_config(self, study_data: FileStudyTreeConfig) -> t.Tuple[CommandOutput, t.Dict[str, t.Any]]:
        return (
            CommandOutput(
                status=True,
                message=f"Matrix '{self.target}' has been successfully replaced.",
            ),
            {},
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
        return str(self.command_name.value + MATCH_SIGNATURE_SEPARATOR + self.target)

    def match(self, other: ICommand, equal: bool = False) -> bool:
        if not isinstance(other, ReplaceMatrix):
            return False
        if equal:
            return self.target == other.target and self.matrix == other.matrix
        return self.target == other.target

    def _create_diff(self, other: "ICommand") -> t.List["ICommand"]:
        return [other]

    def get_inner_matrices(self) -> t.List[str]:
        assert_this(isinstance(self.matrix, str))
        return [strip_matrix_protocol(self.matrix)]
