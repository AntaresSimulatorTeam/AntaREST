from typing import Any, Optional, List, Tuple, Dict

from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.create_district import (
    DistrictBaseFilter,
)
from antarest.study.storage.variantstudy.model.command.icommand import (
    ICommand,
    MATCH_SIGNATURE_SEPARATOR,
)
from antarest.study.storage.variantstudy.model.model import CommandDTO


class UpdateDistrict(ICommand):
    id: str
    base_filter: Optional[DistrictBaseFilter]
    filter_items: Optional[List[str]]
    output: Optional[bool]
    comments: Optional[str]

    def __init__(self, **data: Any) -> None:
        super().__init__(
            command_name=CommandName.UPDATE_DISTRICT, version=1, **data
        )

    def _apply_config(
        self, study_data: FileStudyTreeConfig
    ) -> Tuple[CommandOutput, Dict[str, Any]]:
        base_set = study_data.sets[self.id]
        if self.id not in study_data.sets:
            return (
                CommandOutput(
                    status=False,
                    message=f"District '{self.id}' does not exist and should be created",
                ),
                dict(),
            )

        if self.base_filter:
            base_filter = self.base_filter or DistrictBaseFilter.remove_all
            inverted_set = base_filter == DistrictBaseFilter.add_all
        else:
            inverted_set = base_set.inverted_set
        study_data.sets[self.id].areas = self.filter_items or base_set.areas
        study_data.sets[self.id].output = (
            self.output if self.output is not None else base_set.output
        )
        study_data.sets[self.id].inverted_set = inverted_set

        item_key = "-" if inverted_set else "+"
        return CommandOutput(status=True, message=self.id), {
            "district_id": self.id,
            "item_key": item_key,
        }

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        output, data = self._apply_config(study_data.config)
        if not output.status:
            return output
        sets = study_data.tree.get(["input", "areas", "sets"])
        district_id = data["district_id"]
        item_key = data["item_key"]
        apply_filter = (
            self.base_filter.value
            if self.base_filter
            else sets.get("apply-filter", DistrictBaseFilter.remove_all)
        )
        study_data.tree.save(
            {
                "caption": sets[district_id]["caption"],
                "apply-filter": apply_filter,
                item_key: self.filter_items,
                "output": study_data.config.sets[district_id].output,
                "comments": self.comments,
            },
            ["input", "areas", "sets", district_id],
        )

        return output

    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.UPDATE_DISTRICT.value,
            args={
                "id": self.id,
                "base_filter": self.base_filter.value
                if self.base_filter
                else None,
                "filter_items": self.filter_items,
                "output": self.output,
                "comments": self.comments,
            },
        )

    def match_signature(self) -> str:
        return str(
            self.command_name.value + MATCH_SIGNATURE_SEPARATOR + self.id
        )

    def match(self, other: ICommand, equal: bool = False) -> bool:
        if not isinstance(other, UpdateDistrict):
            return False
        simple_match = self.id == other.id
        if not equal:
            return simple_match
        return (
            simple_match
            and self.base_filter == other.base_filter
            and self.filter_items == other.filter_items
            and self.output == other.output
            and self.comments == other.comments
        )

    def _create_diff(self, other: "ICommand") -> List["ICommand"]:
        return [other]

    def get_inner_matrices(self) -> List[str]:
        return []
