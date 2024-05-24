import copy
from typing import Any, Dict, List, Tuple, Union

from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.model import CommandDTO


class UpdateScenarioBuilder(ICommand):
    """
    Command used to update a scenario builder table.
    """

    command_name = CommandName.UPDATE_SCENARIO_BUILDER
    version = 1
    data: Dict[str, Any]

    @staticmethod
    def parse_key(key: str) -> Tuple[str, List[str], str]:
        parts = key.split(",")
        symbol = parts[0]

        if symbol == "ntc":  # NTC links scenarios
            index = parts[3]  # ntc,z1,z2,0 -> index is the year
        elif symbol in ["t", "r"]:  # Clusters may include an additional identifier
            index = parts[2]  # t,z1,0,cluster1 -> index is the year
        else:  # Generic areas scenarios.
            index = parts[2]  # l,z1,0 -> index is the year

        return symbol, parts, index

    @staticmethod
    def insert_by_symbol(existing_data: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merges and sorts configuration data by ruleset keys using a defined sorting mechanism.

        This method updates existing configuration data with new entries, ensuring data integrity and order. For each ruleset in the configuration:
        - If the ruleset does not exist in `existing_data`, it is added.
        - If it exists, the new data is merged with the existing data, and the combined data is sorted.

        Sorting is based on the key structure, parsed by the `parse_key` function, which prioritizes symbol, area, and index.
        Non-standard or malformed keys are handled gracefully by assigning them a high sort value.

        Parameters:
        - existing_data: The current configuration data where keys represent rulesets.
        - new_data: New data to merge, following the same structure as `existing_data`.

        Returns:
        - Updated and sorted configuration data.

        Example:
        Given `existing_data` as {'Default Ruleset': {'l,a,0': 10, 'l,a,2': 30}} and `new_data` as {'Default Ruleset': {'l,a,1': 20}},
        the result would be {'Default Ruleset': {'l,a,0': 10, 'l,a,1': 20, 'l,a,2': 30}}.
        """
        result = copy.deepcopy(existing_data)

        for ruleset, ruleset_data in new_data.items():
            if ruleset not in result:
                result[ruleset] = ruleset_data  # Add the entire new ruleset if it doesn't exist
            else:
                # Merge new data into the existing ruleset and then sort the keys
                merged_data = {**result[ruleset], **ruleset_data}
                sorted_keys = sorted(merged_data.keys(), key=lambda k: UpdateScenarioBuilder.parse_key(k))
                # Reassign the sorted dictionary back to the result under the current ruleset
                result[ruleset] = {k: merged_data[k] for k in sorted_keys}

        return result

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        url = ["settings", "scenariobuilder"]
        existing_config = study_data.tree.get(url)
        updated_config = UpdateScenarioBuilder.insert_by_symbol(existing_config, self.data)
        study_data.tree.save(updated_config, url)
        return CommandOutput(status=True)

    def _apply_config(self, study_data: FileStudyTreeConfig) -> Tuple[CommandOutput, Dict[str, Any]]:
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
