from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.input.thermal.series.area.thermal.thermal import (
    InputThermalSeriesAreaThermal,
)


class InputThermalSeriesArea(FolderNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        area: str,
    ):
        FolderNode.__init__(self, context, config)
        self.area = area

    def build(self) -> TREE:
        # Note that cluster IDs are case-insensitive, but series IDs are in lower case.
        # For instance, if your cluster ID is "Base", then the series ID will be "base".
        series_ids = map(str.lower, self.config.get_thermal_ids(self.area))
        children: TREE = {
            series_id: InputThermalSeriesAreaThermal(self.context, self.config.next_file(series_id))
            for series_id in series_ids
        }
        return children
