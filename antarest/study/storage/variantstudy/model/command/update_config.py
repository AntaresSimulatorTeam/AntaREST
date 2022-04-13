import logging
from pathlib import Path
from typing import Any, Union, List, Tuple, Dict, Optional

from antarest.core.model import JSON
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    ChildNotFoundError,
)
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import (
    IniFileNode,
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


class UpdateConfig(ICommand):
    target: str
    data: Union[str, int, float, bool, JSON]

    def __init__(self, **data: Any) -> None:
        super().__init__(
            command_name=CommandName.UPDATE_CONFIG, version=1, **data
        )

    def _apply_config(
        self, study_data: FileStudyTreeConfig
    ) -> Tuple[CommandOutput, Dict[str, Any]]:
        return CommandOutput(status=True, message="ok"), dict()

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        url = self.target.split("/")
        tree_node = study_data.tree.get_node(url)
        if not isinstance(tree_node, IniFileNode):
            return CommandOutput(
                status=False,
                message=f"Study node at path {self.target} is invalid",
            )

        study_data.tree.save(self.data, url)
        output, _ = self._apply_config(study_data.config)
        return output

    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.UPDATE_CONFIG.value,
            args={
                "target": self.target,
                "data": self.data,
            },
        )

    def match_signature(self) -> str:
        return str(
            self.command_name.value + MATCH_SIGNATURE_SEPARATOR + self.target
        )

    def match(self, other: ICommand, equal: bool = False) -> bool:
        if not isinstance(other, UpdateConfig):
            return False
        simple_match = self.target == other.target
        if not equal:
            return simple_match
        return simple_match and self.data == other.data

    def revert(
        self, history: List["ICommand"], base: FileStudy
    ) -> List["ICommand"]:
        update_config_list: List[UpdateConfig] = []
        self_target_path = Path(self.target)
        parent_path: Optional[Path] = None
        for command in reversed(history):
            if isinstance(command, UpdateConfig):
                # adding all the UpdateConfig commands until we find one containing self (or the end)
                update_config_list.append(command)
            if (
                Path(command.target) in self_target_path.parents
                or command.target == self.target
            ):
                # found the last parent command.
                parent_path = Path(command.target)
                break

        if parent_path is not None:
            # we found the last parent command which is in the end of the list
            # we now revert the list of UpdateConfig commands to return it in the correct order
            # and we also filter out the UpdateConfig commands which are not "children" of the parent command
            output_list: List[UpdateConfig] = [
                command
                for command in update_config_list[::-1]
                if parent_path in Path(command.target).parents
                or str(parent_path) == command.target
            ]
            return output_list

        from antarest.study.storage.variantstudy.model.command.utils_extractor import (
            CommandExtraction,
        )

        try:
            return [
                (
                    self.command_context.command_extractor
                    or CommandExtraction(self.command_context.matrix_service)
                ).generate_update_config(base.tree, self.target.split("/"))
            ]
        except ChildNotFoundError as e:
            logging.getLogger(__name__).warning(
                f"Failed to extract revert command for update_config {self.target}",
                exc_info=e,
            )
            return []

    def _create_diff(self, other: "ICommand") -> List["ICommand"]:
        return [other]

    def get_inner_matrices(self) -> List[str]:
        return []
