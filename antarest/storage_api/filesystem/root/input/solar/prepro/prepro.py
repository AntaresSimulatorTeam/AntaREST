from antarest.storage_api.filesystem.config.model import StudyConfig
from antarest.storage_api.filesystem.folder_node import FolderNode
from antarest.storage_api.filesystem.inode import TREE
from antarest.storage_api.filesystem.root.input.solar.prepro.area.area import (
    InputSolarPreproArea,
)
from antarest.storage_api.filesystem.root.input.solar.prepro.correlation import (
    InputSolarPreproCorrelation,
)


class InputSolarPrepro(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {
            a: InputSolarPreproArea(config.next_file(a))
            for a in config.area_names()
        }
        children["correlation"] = InputSolarPreproCorrelation(
            config.next_file("correlation.ini")
        )
        return children
