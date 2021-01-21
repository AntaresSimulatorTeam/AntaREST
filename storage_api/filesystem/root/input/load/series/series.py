from storage_api.filesystem.config.model import Config
from storage_api.filesystem.folder_node import FolderNode
from storage_api.filesystem.inode import TREE
from storage_api.filesystem.root.input.load.series.area import (
    InputLoadSeriesArea,
)


class InputLoadSeries(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {
            f"load_{a}": InputLoadSeriesArea(config.next_file(f"load_{a}.txt"))
            for a in config.area_names()
        }
        return children
