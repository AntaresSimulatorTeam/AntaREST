from antarest.storage.repository.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.input.solar.prepro.area.area import (
    InputSolarPreproArea,
)
from antarest.storage.repository.filesystem.root.input.solar.prepro.correlation import (
    InputSolarPreproCorrelation,
)


class InputSolarPrepro(FolderNode):
    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            a: InputSolarPreproArea(self.context, config.next_file(a))
            for a in config.area_names()
        }
        children["correlation"] = InputSolarPreproCorrelation(
            self.context, config.next_file("correlation.ini")
        )
        return children
