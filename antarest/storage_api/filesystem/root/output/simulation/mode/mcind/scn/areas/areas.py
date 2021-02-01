from antarest.storage_api.filesystem.config.model import Config
from antarest.storage_api.filesystem.folder_node import FolderNode
from antarest.storage_api.filesystem.inode import TREE
from antarest.storage_api.filesystem.root.output.simulation.mode.mcind.scn.areas.item.area import (
    OutputSimulationModeMcIndScnAreasArea as Area,
)
from antarest.storage_api.filesystem.root.output.simulation.mode.mcind.scn.areas.item.set import (
    OutputSimulationModeMcIndScnAreasSet as Set,
)


class OutputSimulationModeMcIndScnAreas(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {
            a: Area(config.next_file(a), area=a) for a in config.area_names()
        }

        for s in config.set_names():
            children[f"@ {s}"] = Set(config.next_file(f"@ {s}"), set=s)
        return children
