from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig, Simulation
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.mcall.mcall import (
    OutputSimulationModeMcAll,
)
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.mcind.mcind import (
    OutputSimulationModeMcInd,
)


class OutputSimulationMode(FolderNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        simulation: Simulation,
    ):
        FolderNode.__init__(self, context, config)
        self.simulation = simulation

    def build(self) -> TREE:
        children: TREE = {}
        # todo: il faut aussi le faire pour ts-numbers ...
        # todo: il manque le set mais j'ai pas compris ce que c'est ...
        # todo: il manque le filtre sur les annual, monthly etc. sur les areas.
        # todo: essayer de refactor le if "" in folder : ...
        # todo: que faire du updated-links ?? sa structure dépend de la version ... C'est giga relou.

        if self.simulation.by_year:
            children["mc-ind"] = OutputSimulationModeMcInd(
                self.context, self.config.next_file("mc-ind"), self.simulation
            )
        if self.simulation.synthesis:
            children["mc-all"] = OutputSimulationModeMcAll(
                self.context, self.config.next_file("mc-all"), self.simulation
            )

        return children
