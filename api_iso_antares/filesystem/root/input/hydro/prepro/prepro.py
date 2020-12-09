from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.input.hydro.prepro.area.area import (
    InputHydroPreproArea,
)
from api_iso_antares.filesystem.root.input.hydro.prepro.correlation import (
    InputHydroPreproCorrelation,
)


class InputHydroPrepro(FolderNode):
    def __init__(self, config: Config):
        children: TREE = {
            a: InputHydroPreproArea(config.next_file(a))
            for a in config.area_names
        }
        children["correlation"] = InputHydroPreproCorrelation(
            config.next_file("correlation.ini")
        )
        FolderNode.__init__(self, children)
