from antarest.storage_api.filesystem.config.model import Config
from antarest.storage_api.filesystem.folder_node import FolderNode
from antarest.storage_api.filesystem.inode import TREE
from antarest.storage_api.filesystem.root.input.hydro.prepro.area.area import (
    InputHydroPreproArea,
)
from antarest.storage_api.filesystem.root.input.hydro.prepro.correlation import (
    InputHydroPreproCorrelation,
)


class InputHydroPrepro(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {
            a: InputHydroPreproArea(config.next_file(a))
            for a in config.area_names()
        }
        children["correlation"] = InputHydroPreproCorrelation(
            config.next_file("correlation.ini")
        )
        return children
