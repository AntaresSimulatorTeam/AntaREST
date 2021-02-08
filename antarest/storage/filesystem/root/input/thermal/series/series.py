from antarest.storage.filesystem.config.model import StudyConfig
from antarest.storage.filesystem.folder_node import FolderNode
from antarest.storage.filesystem.inode import TREE
from antarest.storage.filesystem.root.input.thermal.series.area.area import (
    InputThermalSeriesArea,
)


class InputThermalSeries(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {
            a: InputThermalSeriesArea(config.next_file(a), area=a)
            for a in config.area_names()
        }
        return children
