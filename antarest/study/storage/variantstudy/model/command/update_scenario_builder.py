from typing import Any, Dict, List, Tuple

from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.model import CommandDTO


class UpdateScenarioBuilder(ICommand):
    """
    Command used to update a scenario builder table.
    """

    # Overloaded metadata
    # ===================

    command_name = CommandName.UPDATE_SCENARIO_BUILDER
    version = 1

    # Command parameters
    # ==================

    data: Dict[str, Any]

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        """
        Apply the command to the study data.

        This method updates the current configuration of the scenario builder data.
        It adds, modifies, or removes section values based on the command's data.
        The changes are saved to the study's tree structure.

        Args:
            study_data: The study data to which the command will be applied.

        Returns:
            CommandOutput: The output of the command, indicating the status of the operation.
        """
        url = ["settings", "scenariobuilder"]

        curr_cfg = study_data.tree.get(url)
        for section_name, section in list(self.data.items()):
            if section:
                curr_section = curr_cfg.setdefault(section_name, {})
                for key, value in section.items():
                    if isinstance(value, (int, float)) and value != float("nan"):
                        curr_section[key] = value
                    else:
                        curr_section.pop(key, None)
            else:
                curr_cfg.pop(section_name, None)

        study_data.tree.save(curr_cfg, url)
        return CommandOutput(status=True)

    def _apply_config(self, study_data: FileStudyTreeConfig) -> Tuple[CommandOutput, Dict[str, Any]]:
        return CommandOutput(status=True), {}

    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.UPDATE_SCENARIO_BUILDER.value,
            args={"data": self.data},
        )

    def match_signature(self) -> str:
        return CommandName.UPDATE_SCENARIO_BUILDER.value

    def match(self, other: "ICommand", equal: bool = False) -> bool:
        if not isinstance(other, UpdateScenarioBuilder):
            return False
        if equal:
            return self.data == other.data
        return True

    def _create_diff(self, other: "ICommand") -> List["ICommand"]:
        return [other]

    def get_inner_matrices(self) -> List[str]:
        return []
