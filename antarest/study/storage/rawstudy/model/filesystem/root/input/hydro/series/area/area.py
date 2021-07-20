from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.input.hydro.series.area.mod import (
    InputHydroSeriesAreaMod,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.hydro.series.area.ror import (
    InputHydroSeriesAreaRor,
)


class InputHydroSeriesArea(FolderNode):
    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            "mod": InputHydroSeriesAreaMod(
                self.context, config.next_file("mod.txt")
            ),
            "ror": InputHydroSeriesAreaRor(
                self.context, config.next_file("ror.txt")
            ),
        }
        return children
