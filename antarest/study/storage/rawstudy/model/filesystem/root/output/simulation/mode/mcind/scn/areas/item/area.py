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
from antarest.study.storage.rawstudy.model.filesystem.matrix.output_series_matrix import (
    AreaOutputSeriesMatrix,
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
                children[f"details-{timing}"] = AreaOutputSeriesMatrix(
                    self.context,
                    config.next_file(f"details-{timing}.txt"),
                    timing,
                    self.area,
                )

            if (
                self.config.enr_modelling == "clusters"
                and len(
                    config.get_thermal_names(self.area, only_enabled=True),
                )
                > 0
            ):
                children[f"details-res-{timing}"] = AreaOutputSeriesMatrix(
                    self.context,
                    config.next_file(f"details-res-{timing}.txt"),
                    timing,
                    self.area,
                )

            children[f"values-{timing}"] = AreaOutputSeriesMatrix(
                self.context,
                config.next_file(f"values-{timing}.txt"),
                timing,
                self.area,
            )

        return children
