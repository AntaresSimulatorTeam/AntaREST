from enum import Enum
from typing import Any, Optional, List, cast, Tuple, Dict

from pydantic import validator

from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    transform_name_to_id,
    DistrictSet,
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.icommand import (
    ICommand,
    MATCH_SIGNATURE_SEPARATOR,
)
from antarest.study.storage.variantstudy.model.model import CommandDTO


class DistrictBaseFilter(Enum):
    add_all = "add-all"
    remove_all = "remove-all"


class CreateDistrict(ICommand):
    name: str
    base_filter: Optional[DistrictBaseFilter] = None
    filter_items: Optional[List[str]] = None
    output: bool = True
    comments: str = ""

    def __init__(self, **data: Any) -> None:
        super().__init__(
            command_name=CommandName.CREATE_DISTRICT, version=1, **data
        )

    @validator("name")
    def validate_district_name(cls, val: str) -> str:
        valid_name = transform_name_to_id(val, lower=False)
        if valid_name != val:
            raise ValueError(
                "Area name must only contains [a-zA-Z0-9],&,-,_,(,) characters"
            )
        return val

    def _apply_config(
        self, study_data: FileStudyTreeConfig
    ) -> Tuple[CommandOutput, Dict[str, Any]]:
        district_id = transform_name_to_id(self.name)
        if district_id in study_data.sets:
            return (
                CommandOutput(
                    status=False,
                    message=f"District '{self.name}' already exists and could not be created",
                ),
                dict(),
            )

        base_filter = self.base_filter or DistrictBaseFilter.remove_all
        inverted_set = base_filter == DistrictBaseFilter.add_all
        study_data.sets[district_id] = DistrictSet(
            name=self.name,
            areas=self.filter_items or [],
            output=self.output,
            inverted_set=inverted_set,
        )
        item_key = "-" if inverted_set else "+"
        return CommandOutput(status=True, message=district_id), {
            "district_id": district_id,
            "item_key": item_key,
        }

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        output, data = self._apply_config(study_data.config)
        if not output.status:
            return output
        district_id = data["district_id"]
        item_key = data["item_key"]
        study_data.tree.save(
            {
                "caption": self.name,
                "apply-filter": (
                    self.base_filter or DistrictBaseFilter.remove_all
                ).value,
                item_key: self.filter_items or [],
                "output": study_data.config.sets[district_id].output,
                "comments": self.comments,
            },
            ["input", "areas", "sets", district_id],
        )

        return output

    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.CREATE_DISTRICT.value,
            args={
                "name": self.name,
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
            self.command_name.value + MATCH_SIGNATURE_SEPARATOR + self.name
        )

    def match(self, other: ICommand, equal: bool = False) -> bool:
        if not isinstance(other, CreateDistrict):
            return False
        simple_match = self.name == other.name
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
        other = cast(CreateDistrict, other)
        district_id = transform_name_to_id(self.name)
        from antarest.study.storage.variantstudy.model.command.update_config import (
            UpdateConfig,
        )

        base_filter = other.base_filter or DistrictBaseFilter.remove_all
        inverted_set = base_filter == DistrictBaseFilter.add_all
        item_key = "-" if inverted_set else "+"
        return [
            UpdateConfig(
                target=f"input/areas/sets/{district_id}",
                data={
                    "caption": other.name,
                    "apply-filter": (
                        other.base_filter or DistrictBaseFilter.remove_all
                    ).value,
                    item_key: other.filter_items or [],
                    "output": other.output,
                    "comments": other.comments,
                },
                command_context=self.command_context,
            )
        ]

    def get_inner_matrices(self) -> List[str]:
        return []
