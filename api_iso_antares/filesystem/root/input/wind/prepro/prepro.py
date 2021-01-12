from api_iso_antares.filesystem.config.model import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.input.wind.prepro.area.area import (
    InputWindPreproArea,
)
from api_iso_antares.filesystem.root.input.wind.prepro.correlation import (
    InputWindPreproCorrelation,
)


class InputWindPrepro(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {
            a: InputWindPreproArea(config.next_file(a))
            for a in config.area_names
        }
        children["correlation"] = InputWindPreproCorrelation(
            config.next_file("correlation.ini")
        )
        return children
