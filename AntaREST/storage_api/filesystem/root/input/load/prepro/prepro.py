from AntaREST.storage_api.filesystem.config.model import Config
from AntaREST.storage_api.filesystem.folder_node import FolderNode
from AntaREST.storage_api.filesystem.inode import TREE
from AntaREST.storage_api.filesystem.root.input.load.prepro.area.area import (
    InputLoadPreproArea,
)
from AntaREST.storage_api.filesystem.root.input.load.prepro.correlation import (
    InputLoadPreproCorrelation,
)


class InputLoadPrepro(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {
            a: InputLoadPreproArea(config.next_file(a))
            for a in config.area_names()
        }
        children["correlation"] = InputLoadPreproCorrelation(
            config.next_file("correlation.ini")
        )
        return children
