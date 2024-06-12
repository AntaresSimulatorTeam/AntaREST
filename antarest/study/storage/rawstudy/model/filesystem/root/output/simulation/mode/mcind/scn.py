from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.common.utils import OUTPUT_MAPPING


class OutputSimulationModeMcIndScn(FolderNode):
    def build(self) -> TREE:
        if not self.config.output_path:
            return {}
        children: TREE = {}
        for key, simulation_class in OUTPUT_MAPPING.items():
            if (self.config.path / key).exists():
                children[key] = simulation_class(self.context, self.config.next_file(key))
        return children
