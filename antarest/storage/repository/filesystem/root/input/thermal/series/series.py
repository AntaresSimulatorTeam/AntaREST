from antarest.storage.repository.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.input.thermal.series.area.area import (
    InputThermalSeriesArea,
)


class InputThermalSeries(FolderNode):
    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            a: InputThermalSeriesArea(
                self.context, config.next_file(a), area=a
            )
            for a in config.area_names()
        }
        return children
