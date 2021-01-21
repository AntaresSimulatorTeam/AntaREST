from storage_api.filesystem.config.model import Config
from storage_api.filesystem.folder_node import FolderNode
from storage_api.filesystem.inode import TREE
from storage_api.filesystem.root.input.load.prepro.prepro import (
    InputLoadPrepro,
)
from storage_api.filesystem.root.input.load.series.series import (
    InputLoadSeries,
)


class InputLoad(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {
            "prepro": InputLoadPrepro(config.next_file("prepro")),
            "series": InputLoadSeries(config.next_file("series")),
        }
        return children
