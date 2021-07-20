from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.input.load.series.area import (
    InputLoadSeriesArea,
)


class InputLoadSeries(FolderNode):
    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            f"load_{a}": InputLoadSeriesArea(
                self.context, config.next_file(f"load_{a}.txt")
            )
            for a in config.area_names()
        }
        return children
