from storage_api.filesystem.config.model import Config
from storage_api.filesystem.folder_node import FolderNode
from storage_api.filesystem.inode import TREE
from storage_api.filesystem.root.input.hydro.series.area.area import (
    InputHydroSeriesArea,
)


class InputHydroSeries(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {
            a: InputHydroSeriesArea(config.next_file(a))
            for a in config.area_names()
        }
        return children
