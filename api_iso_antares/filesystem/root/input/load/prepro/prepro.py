from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.input.load.prepro.area.area import (
    InputLoadPreproArea,
)
from api_iso_antares.filesystem.root.input.load.prepro.correlation import (
    InputLoadPreproCorrelation,
)


class InputLoadPrepro(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {
            a: InputLoadPreproArea(config.next_file(a))
            for a in config.area_names
        }
        children["correlation"] = InputLoadPreproCorrelation(
            config.next_file("correlation.ini")
        )
        return children
