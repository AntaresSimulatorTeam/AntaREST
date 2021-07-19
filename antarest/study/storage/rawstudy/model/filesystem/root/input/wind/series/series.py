from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.input.wind.series.area import (
    InputWindSeriesArea,
)


class InputWindSeries(FolderNode):
    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            f"wind_{a}": InputWindSeriesArea(
                self.context, config.next_file(f"wind_{a}.txt")
            )
            for a in config.area_names()
        }
        return children
