from antarest.storage.repository.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.repository.filesystem.context import ContextServer
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.output.simulation.mode.mcind.scn.areas.item.details import (
    OutputSimulationModeMcIndScnAreasItemDetails as Details,
)

from antarest.storage.repository.filesystem.root.output.simulation.mode.mcind.scn.areas.item.values import (
    OutputSimulationModeMcIndScnAreasItemValues as Values,
)


class OutputSimulationModeMcIndScnAreasArea(FolderNode):
    def __init__(
        self, context: ContextServer, config: FileStudyTreeConfig, area: str
    ):
        FolderNode.__init__(self, context, config)
        self.area = area

    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = dict()

        for timing in config.get_filters_year(self.area):
            # detail files only exists when there is thermal cluster to be detailed
            if (
                len(
                    config.get_thermal_names(self.area, only_enabled=True),
                )
                > 0
            ):
                children[f"details-{timing}"] = Details(
                    self.context,
                    config.next_file(f"details-{timing}.txt"),
                    timing,
                    self.area,
                )

            children[f"values-{timing}"] = Values(
                self.context,
                config.next_file(f"values-{timing}.txt"),
                timing,
                self.area,
            )

        return children
