from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
    ENR_MODELLING,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.output_series_matrix import (
    AreaOutputSeriesMatrix,
)


class OutputSimulationModeMcAllAreasArea(FolderNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        area: str,
    ):
        FolderNode.__init__(self, context, config)
        self.area = area

    def build(self) -> TREE:
        children: TREE = dict()

        filters = self.config.get_filters_synthesis(self.area)

        for freq in filters:
            children[f"id-{freq}"] = AreaOutputSeriesMatrix(
                self.context,
                self.config.next_file(f"id-{freq}.txt"),
                freq,
                self.area,
            )

            children[f"values-{freq}"] = AreaOutputSeriesMatrix(
                self.context,
                self.config.next_file(f"values-{freq}.txt"),
                freq,
                self.area,
            )

            if (
                len(
                    self.config.get_thermal_names(
                        self.area, only_enabled=True
                    ),
                )
                > 0
            ):
                children[f"details-{freq}"] = AreaOutputSeriesMatrix(
                    self.context,
                    self.config.next_file(f"details-{freq}.txt"),
                    freq,
                    self.area,
                )

            if (
                self.config.enr_modelling == ENR_MODELLING.CLUSTERS.value
                and len(
                    self.config.get_renewable_names(
                        self.area, only_enabled=True
                    ),
                )
                > 0
            ):
                children[f"details-res-{freq}"] = AreaOutputSeriesMatrix(
                    self.context,
                    self.config.next_file(f"details-res-{freq}.txt"),
                    freq,
                    self.area,
                )

        return children
