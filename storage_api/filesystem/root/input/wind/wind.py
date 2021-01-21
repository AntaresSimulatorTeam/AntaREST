from storage_api.filesystem.config.model import Config
from storage_api.filesystem.folder_node import FolderNode
from storage_api.filesystem.inode import TREE
from storage_api.filesystem.root.input.wind.prepro.prepro import (
    InputWindPrepro,
)
from storage_api.filesystem.root.input.wind.series.series import (
    InputWindSeries,
)


class InputWind(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {
            "prepro": InputWindPrepro(config.next_file("prepro")),
            "series": InputWindSeries(config.next_file("series")),
        }
        return children
