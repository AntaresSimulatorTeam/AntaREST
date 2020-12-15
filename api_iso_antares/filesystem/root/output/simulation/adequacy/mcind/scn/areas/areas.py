from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.output.simulation.adequacy.mcind.scn.areas.item.item import (
    OutputSimulationAdequacyMcIndScnAreasItem as Item,
)


class OutputSimulationAdequacyMcIndScnAreas(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {
            a: Item(config.next_file(a), area=a) for a in config.area_names
        }
        return children
