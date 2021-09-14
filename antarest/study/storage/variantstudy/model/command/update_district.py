from typing import Dict, List, Any, Optional

from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.create_district import (
    DistrictBaseFilter,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand


class UpdateDistrict(ICommand):
    id: str
    name: str
    metadata: Dict[str, str]
    base_filter: Optional[DistrictBaseFilter]
    filter_items: Optional[List[str]]
    output: Optional[bool]

    def __init__(self, **data: Any) -> None:
        super().__init__(
            command_name=CommandName.UPDATE_DISTRICT, version=1, **data
        )

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        raise NotImplementedError()

    def revert(self, study_data: FileStudy) -> CommandOutput:
        raise NotImplementedError()
