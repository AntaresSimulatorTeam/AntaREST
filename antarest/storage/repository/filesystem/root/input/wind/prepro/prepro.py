from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.input.wind.prepro.area.area import (
    InputWindPreproArea,
)
from antarest.storage.repository.filesystem.root.input.wind.prepro.correlation import (
    InputWindPreproCorrelation,
)


class InputWindPrepro(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {
            a: InputWindPreproArea(config.next_file(a))
            for a in config.area_names()
        }
        children["correlation"] = InputWindPreproCorrelation(
            config.next_file("correlation.ini")
        )
        return children
