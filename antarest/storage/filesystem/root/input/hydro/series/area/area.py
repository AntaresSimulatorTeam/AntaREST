from antarest.storage.filesystem.config.model import StudyConfig
from antarest.storage.filesystem.folder_node import FolderNode
from antarest.storage.filesystem.inode import TREE
from antarest.storage.filesystem.root.input.hydro.series.area.mod import (
    InputHydroSeriesAreaMod,
)
from antarest.storage.filesystem.root.input.hydro.series.area.ror import (
    InputHydroSeriesAreaRor,
)


class InputHydroSeriesArea(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {
            "mod": InputHydroSeriesAreaMod(config.next_file("mod.txt")),
            "ror": InputHydroSeriesAreaRor(config.next_file("ror.txt")),
        }
        return children
