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
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import (
    MatrixFrequency,
)
from antarest.study.storage.rawstudy.model.filesystem.matrix.output_series_matrix import (
    AreaOutputSeriesMatrix,
)


class OutputSimulationAreaItem(FolderNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        area: str,
        mc_all: bool = True,
    ):
        FolderNode.__init__(self, context, config)
        self.area = area
        self.mc_all = mc_all

    def build(self) -> TREE:
        children: TREE = {}

        # filters = self.config.get_filters_synthesis(self.area)
        # todo get the config related to this output (now this may fail if input has changed since the launch)

        freq: MatrixFrequency
        for freq in MatrixFrequency:
            if self.mc_all:
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

            # has_thermal_clusters = len(self.config.get_thermal_names(self.area, only_enabled=True)) > 0
            # todo get the config related to this output (now this may fail if input has changed since the launch)
            has_thermal_clusters = True

            if has_thermal_clusters:
                children[f"details-{freq}"] = AreaOutputSeriesMatrix(
                    self.context,
                    self.config.next_file(f"details-{freq}.txt"),
                    freq,
                    self.area,
                )

            # has_enr_clusters = self.config.enr_modelling == ENR_MODELLING.CLUSTERS.value and
            # len(self.config.get_renewable_names(self.area, only_enabled=True)) > 0
            # todo get the config related to this output (now this may fail if input has changed since the launch)
            has_enr_clusters = True

            if has_enr_clusters:
                children[f"details-res-{freq}"] = AreaOutputSeriesMatrix(
                    self.context,
                    self.config.next_file(f"details-res-{freq}.txt"),
                    freq,
                    self.area,
                )

            # add condition len(self.config.get_short_term_storage_names(self.area, only_enabled=True)) > 0 to
            # has_short_term_storage boolean
            # todo get the config related to this output (now this may fail if input has changed since the launch)

            has_short_term_storage = self.config.version >= 860
            if has_short_term_storage:
                children[f"details-STstorage-{freq}"] = AreaOutputSeriesMatrix(
                    self.context,
                    self.config.next_file(f"details-STstorage-{freq}.txt"),
                    freq,
                    self.area,
                )

        return {
            child: children[child]
            for child in children
            # this takes way too long in zip mode... see above todo to prevent needing this
            # if cast(AreaOutputSeriesMatrix, children[child]).file_exists()
        }
