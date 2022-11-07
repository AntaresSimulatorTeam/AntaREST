from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
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
    def build(self) -> TREE:
        children: TREE = {
            "areas": OutputSimulationAreas(
                self.context, self.config.next_file("areas"), mc_all=False
            ),
            "links": OutputSimulationLinks(
                self.context, self.config.next_file("links"), mc_all=False
            ),
            "binding_constraints": OutputSimulationBindingConstraintItem(
                self.context, self.config.next_file("binding_constraints")
            ),
        }
        return children
