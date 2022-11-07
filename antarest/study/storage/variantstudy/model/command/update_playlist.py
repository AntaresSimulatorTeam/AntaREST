from typing import List, Tuple, Dict, Any, Optional

from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.helpers import FileStudyHelpers
from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)

from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.model import CommandDTO


class UpdatePlaylist(ICommand):
    active: bool
    items: Optional[List[int]] = None
    weights: Optional[Dict[int, float]] = None
    reverse: bool = False

    def __init__(self, **data: Any) -> None:
        super().__init__(
            command_name=CommandName.UPDATE_PLAYLIST, version=1, **data
        )

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        FileStudyHelpers.set_playlist(
            study_data,
            self.items or [],
            self.weights,
            reverse=self.reverse,
            active=self.active,
        )
        return CommandOutput(status=True)

    def _apply_config(
        self, study_data: FileStudyTreeConfig
    ) -> Tuple[CommandOutput, Dict[str, Any]]:
        return CommandOutput(status=True), {}

    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.UPDATE_PLAYLIST.value,
            args={
                "active": self.active,
                "items": self.items,
                "weights": self.weights,
                "reverse": self.reverse,
            },
        )

    def match_signature(self) -> str:
        return CommandName.UPDATE_PLAYLIST.name

    def match(self, other: "ICommand", equal: bool = False) -> bool:
        if not isinstance(other, UpdatePlaylist):
            return False
        if equal:
            return (
                self.active == other.active
                and self.reverse == other.reverse
                and self.items == other.items
                and self.weights == other.weights
            )
        return True

    def _create_diff(self, other: "ICommand") -> List["ICommand"]:
        return [other]

    def get_inner_matrices(self) -> List[str]:
        return []
