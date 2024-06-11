from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig, Simulation
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.common.areas import (
    OutputSimulationAreas,
)
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.common.binding_const import (
    OutputSimulationBindingConstraintItem,
)
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.common.links import (
    OutputSimulationLinks,
)


class OutputSimulationModeMcIndScn(FolderNode):
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
        current_path = self.config.output_path / self.simulation.get_file() / self.simulation.mode / "mc-ind"
        children: TREE = {}
        folders = [d.name for d in current_path.iterdir()]
        if "areas" in folders:
            children["areas"] = OutputSimulationAreas(
                self.context, self.config.next_file("areas"), current_path / "areas", mc_all=False
            )
        if "links" in folders:
            children["links"] = OutputSimulationLinks(
                self.context, self.config.next_file("links"), current_path / "links", mc_all=False
            )
        if "binding_constraints" in folders:
            children["binding_constraints"] = OutputSimulationBindingConstraintItem(
                self.context, self.config.next_file("binding_constraints"), current_path / "binding_constraints"
            )
        return children
