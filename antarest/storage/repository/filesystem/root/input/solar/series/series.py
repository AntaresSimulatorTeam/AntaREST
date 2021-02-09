from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.input.solar.series.area import (
    InputSolarSeriesArea,
)


class InputSolarSeries(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {
            f"solar_{a}": InputSolarSeriesArea(
                config.next_file(f"solar_{a}.txt")
            )
            for a in config.area_names()
        }
        return children
