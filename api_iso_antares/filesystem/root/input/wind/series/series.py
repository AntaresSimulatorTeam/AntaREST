from api_iso_antares.filesystem.config.model import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.input.wind.series.area import (
    InputWindSeriesArea,
)


class InputWindSeries(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {
            f"wind_{a}": InputWindSeriesArea(config.next_file(f"wind_{a}.txt"))
            for a in config.area_names
        }
        return children
