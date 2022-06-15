import base64
from typing import List, Any, Tuple, Dict

from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.raw_file_node import (
    RawFileNode,
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


class UpdateRawFile(ICommand):
    target: str
    b64Data: str

    def __init__(self, **data: Any) -> None:
        super().__init__(
            command_name=CommandName.UPDATE_FILE, version=1, **data
        )

    def _apply_config(
        self, study_data: FileStudyTreeConfig
    ) -> Tuple[CommandOutput, Dict[str, Any]]:
        return CommandOutput(status=True, message="ok"), {}

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        url = self.target.split("/")
        tree_node = study_data.tree.get_node(url)
        if not isinstance(tree_node, RawFileNode):
            return CommandOutput(
                status=False,
                message=f"Study node at path {self.target} is invalid",
            )

        study_data.tree.save(
            base64.decodebytes(self.b64Data.encode("utf-8")), url
        )
        return CommandOutput(status=True, message="ok")

    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=self.command_name.value,
            args={"target": self.target, "b64Data": self.b64Data},
        )

    def match_signature(self) -> str:
        return str(
            self.command_name.value + MATCH_SIGNATURE_SEPARATOR + self.target
        )

    def match(self, other: ICommand, equal: bool = False) -> bool:
        if not isinstance(other, UpdateRawFile):
            return False
        simple_match = self.target == other.target
        if not equal:
            return simple_match
        return simple_match and self.b64Data == other.b64Data

    def _create_diff(self, other: "ICommand") -> List["ICommand"]:
        return [other]

    def get_inner_matrices(self) -> List[str]:
        return []
