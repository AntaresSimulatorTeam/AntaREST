from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.input.hydro.series.area.mod import (
    InputHydroSeriesAreaMod,
)
from api_iso_antares.filesystem.root.input.hydro.series.area.ror import (
    InputHydroSeriesAreaRor,
)


class InputHydroSeriesArea(FolderNode):
    def __init__(self, config: Config):
        children: TREE = {
            "mod": InputHydroSeriesAreaMod(config.next_file("mod.txt")),
            "ror": InputHydroSeriesAreaRor(config.next_file("ror.txt")),
        }
        FolderNode.__init__(self, config, children)
