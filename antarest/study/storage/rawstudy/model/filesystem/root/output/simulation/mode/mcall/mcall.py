from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig, Simulation
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.common.utils import OUTPUT_MAPPING


class OutputSimulationModeMcAll(FolderNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        simulation: Simulation,
    ):
        FolderNode.__init__(self, context, config)
        self.simulation = simulation

    def build(self) -> TREE:
        if not self.config.output_path:
            return {}
        current_path = self.config.output_path / self.simulation.get_file() / self.simulation.mode / "mc-all"
        children: TREE = {}
        for key, simulation_class in OUTPUT_MAPPING.items():
            if (current_path / key).exists():
                children[key] = simulation_class(self.context, self.config.next_file(key), current_path / key)
        return children
