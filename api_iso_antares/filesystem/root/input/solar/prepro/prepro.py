from api_iso_antares.filesystem.config.model import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.input.solar.prepro.area.area import (
    InputSolarPreproArea,
)
from api_iso_antares.filesystem.root.input.solar.prepro.correlation import (
    InputSolarPreproCorrelation,
)


class InputSolarPrepro(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {
            a: InputSolarPreproArea(config.next_file(a))
            for a in config.area_names()
        }
        children["correlation"] = InputSolarPreproCorrelation(
            config.next_file("correlation.ini")
        )
        return children
