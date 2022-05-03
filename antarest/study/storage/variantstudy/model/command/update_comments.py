from typing import Any, List, Tuple, Dict

from antarest.core.model import JSON
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    ChildNotFoundError,
)
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
    CommandOutput,
)
from antarest.study.storage.variantstudy.model.command.icommand import (
    ICommand,
)
from antarest.study.storage.variantstudy.model.model import CommandDTO


class UpdateComments(ICommand):
    """Update the file contained at settings/comments.txt"""

    comments: str

    def __init__(self, **data: Any) -> None:
        super().__init__(
            command_name=CommandName.UPDATE_COMMENTS, version=1, **data
        )

    def _apply_config(
        self, study_data: FileStudyTreeConfig
    ) -> Tuple[CommandOutput, Dict[str, Any]]:
        return (
            CommandOutput(
                status=True,
                message=f"Comment '{self.comments}' has been successfully replaced.",
            ),
            dict(),
        )

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        replace_comment_data: JSON = {
            "settings": {"comments": self.comments.encode("utf-8")}
        }

        study_data.tree.save(replace_comment_data)

        output, _ = self._apply_config(study_data.config)
        return output

    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.UPDATE_COMMENTS.value,
            args={
                "comments": self.comments,
            },
        )

    def match_signature(self) -> str:
        return str(self.command_name.value)

    def match(self, other: ICommand, equal: bool = False) -> bool:
        if not isinstance(other, UpdateComments):
            return False
        return not equal or (self.comments == other.comments and equal)

    def revert(
        self, history: List["ICommand"], base: FileStudy
    ) -> List["ICommand"]:
        for command in reversed(history):
            if isinstance(command, UpdateComments):
                return [command]

        try:
            return [
                self._get_command_extraction().generate_update_comments(
                    base.tree
                )
            ]
        except ChildNotFoundError:
            return []  # if the file does not exist, there is nothing to revert

    def _create_diff(self, other: "ICommand") -> List["ICommand"]:
        return [other]

    def get_inner_matrices(self) -> List[str]:
        return []
