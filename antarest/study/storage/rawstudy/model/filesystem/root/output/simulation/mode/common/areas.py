from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
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
    ) -> None:
        super().__init__(context, config)

    def build(self) -> TREE:
        areas = set()
        sets = set()
        for file in self.config.path.iterdir():
            name = file.stem
            if "@" in name:
                sets.add(name)
            else:
                areas.add(name)
        children: TREE = {a: Area(self.context, self.config.next_file(a), area=a) for a in areas}

        for s in sets:
            children[f"@ {s}"] = Set(self.context, self.config.next_file(f"@ {s}"), set=s)
        return children
