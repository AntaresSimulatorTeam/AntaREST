from enum import Enum
from typing import Dict, Any, Optional, List

from pydantic import validator

from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    transform_name_to_id,
    Set,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand


class DistrictBaseFilter(Enum):
    add_all = "add-all"
    remove_all = "remove-all"


class CreateDistrict(ICommand):
    name: str
    metadata: Dict[str, str]
    base_filter: Optional[DistrictBaseFilter]
    filter_items: Optional[List[str]]
    output: Optional[bool]
    comments: Optional[str]

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

    def apply(self, study_data: FileStudy) -> CommandOutput:
        district_id = transform_name_to_id(self.name)
        if district_id in study_data.config.sets:
            return CommandOutput(
                status=False,
                message=f"District '{self.name}' already exists and could not be created",
            )

        base_filter = self.base_filter or DistrictBaseFilter.remove_all
        inverted_set = base_filter == DistrictBaseFilter.add_all
        study_data.config.sets[district_id] = Set(
            name=self.name,
            areas=self.filter_items or [],
            output=self.output if self.output is not None else True,
            inverted_set=inverted_set,
        )

        item_key = "-" if inverted_set else "+"
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
        return CommandOutput(status=True, message=district_id)

    def revert(self, study_data: FileStudy) -> CommandOutput:
        raise NotImplementedError()
