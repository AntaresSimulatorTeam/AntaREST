from antarest.storage_api.filesystem.config.model import StudyConfig
from antarest.storage_api.filesystem.folder_node import FolderNode
from antarest.storage_api.filesystem.inode import TREE
from antarest.storage_api.filesystem.root.input.hydro.series.area.area import (
    InputHydroSeriesArea,
)


class InputHydroSeries(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {
            a: InputHydroSeriesArea(config.next_file(a))
            for a in config.area_names()
        }
        return children
