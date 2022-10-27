from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.common.area import (
    OutputSimulationAreaItem as Area,
)
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.common.set import (
    OutputSimulationSet as Set,
)


class OutputSimulationAreas(FolderNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        mc_all: bool = True,
    ) -> None:
        super().__init__(context, config)
        self.mc_all = mc_all

    def build(self) -> TREE:
        children: TREE = {
            a: Area(
                self.context,
                self.config.next_file(a),
                area=a,
                mc_all=self.mc_all,
            )
            for a in self.config.area_names()
        }

        for s in self.config.set_names():
            children[f"@ {s}"] = Set(
                self.context,
                self.config.next_file(f"@ {s}"),
                set=s,
                mc_all=self.mc_all,
            )
        return children
