from AntaREST.storage_api.filesystem.config.model import Config
from AntaREST.storage_api.filesystem.folder_node import FolderNode
from AntaREST.storage_api.filesystem.inode import TREE
from AntaREST.storage_api.filesystem.root.input.wind.prepro.area.area import (
    InputWindPreproArea,
)
from AntaREST.storage_api.filesystem.root.input.wind.prepro.correlation import (
    InputWindPreproCorrelation,
)


class InputWindPrepro(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {
            a: InputWindPreproArea(config.next_file(a))
            for a in config.area_names()
        }
        children["correlation"] = InputWindPreproCorrelation(
            config.next_file("correlation.ini")
        )
        return children
