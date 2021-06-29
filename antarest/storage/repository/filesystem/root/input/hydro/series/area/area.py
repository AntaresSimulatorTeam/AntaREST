from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.input.hydro.series.area.mod import (
    InputHydroSeriesAreaMod,
)
from antarest.storage.repository.filesystem.root.input.hydro.series.area.ror import (
    InputHydroSeriesAreaRor,
)


class InputHydroSeriesArea(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {
            "mod": InputHydroSeriesAreaMod(
                self.context, config.next_file("mod.txt")
            ),
            "ror": InputHydroSeriesAreaRor(
                self.context, config.next_file("ror.txt")
            ),
        }
        return children
