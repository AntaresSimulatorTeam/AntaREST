from antarest.storage.repository.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.input.hydro.series.area.area import (
    InputHydroSeriesArea,
)


class InputHydroSeries(FolderNode):
    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            a: InputHydroSeriesArea(self.context, config.next_file(a))
            for a in config.area_names()
        }
        return children
