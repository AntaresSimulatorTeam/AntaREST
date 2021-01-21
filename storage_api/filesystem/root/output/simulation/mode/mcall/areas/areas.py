from storage_api.filesystem.config.model import Config
from storage_api.filesystem.folder_node import FolderNode
from storage_api.filesystem.inode import TREE
from storage_api.filesystem.root.output.simulation.mode.mcall.areas.item.area import (
    OutputSimulationModeMcAllAreasArea as Area,
)
from storage_api.filesystem.root.output.simulation.mode.mcall.areas.item.set import (
    OutputSimulationModeMcAllAreasSet as Set,
)


class OutputSimulationModeMcAllAreas(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {
            a: Area(config.next_file(a), area=a) for a in config.area_names()
        }

        for s in config.set_names():
            children[f"@ {s}"] = Set(config.next_file(f"@ {s}"), set=s)
        return children
