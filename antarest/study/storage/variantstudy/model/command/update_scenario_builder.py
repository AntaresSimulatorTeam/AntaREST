from typing import List, Tuple, Dict, Any, cast

from antarest.core.utils.dict import merge_deep
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)

from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.model import CommandDTO


class UpdateScenarioBuilder(ICommand):
    data: Dict[str, Any]

    def __init__(self, **data: Any) -> None:
        super().__init__(
            command_name=CommandName.UPDATE_SCENARIO_BUILDER, version=1, **data
        )

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        def remove_empty_value(obj: Dict[str, Any]) -> Dict[str, Any]:
            return {k: v for k, v in obj.items() if v}

        url = ["settings", "scenariobuilder"]
        prev = study_data.tree.get(url)
        new_config = {
            # The value is a string when it is a ruleset cloning
            k: remove_empty_value(v if isinstance(v, dict) else prev[v])
            for k, v in merge_deep(prev, self.data).items()
            # Deleted rulesets have an empty string
            if v != ""
        }
        study_data.tree.save(new_config, url)
        return CommandOutput(status=True)

    def _apply_config(
        self, study_data: FileStudyTreeConfig
    ) -> Tuple[CommandOutput, Dict[str, Any]]:
        return CommandOutput(status=True), {}

    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.UPDATE_SCENARIO_BUILDER.value,
            args={
                "data": self.data,
            },
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
