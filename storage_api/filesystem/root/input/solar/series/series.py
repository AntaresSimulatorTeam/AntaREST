from storage_api.filesystem.config.model import Config
from storage_api.filesystem.folder_node import FolderNode
from storage_api.filesystem.inode import TREE
from storage_api.filesystem.root.input.solar.series.area import (
    InputSolarSeriesArea,
)


class InputSolarSeries(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {
            f"solar_{a}": InputSolarSeriesArea(
                config.next_file(f"solar_{a}.txt")
            )
            for a in config.area_names()
        }
        return children
