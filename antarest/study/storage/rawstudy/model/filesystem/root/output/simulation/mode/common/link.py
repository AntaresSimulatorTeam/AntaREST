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
    LinkOutputSeriesMatrix,
)


class OutputSimulationLinkItem(FolderNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        area: str,
        link: str,
        mc_all: bool = True,
    ):
        FolderNode.__init__(self, context, config)
        self.area = area
        self.link = link
        self.mc_all = mc_all

    def build(self) -> TREE:
        children: TREE = {}

        # filters = self.config.get_filters_synthesis(self.area, self.link)
        # todo get the config related to this output (now this may fail if input has changed since the launch)

        freq: MatrixFrequency
        for freq in MatrixFrequency:
            children[f"values-{freq}"] = LinkOutputSeriesMatrix(
                self.context,
                self.config.next_file(f"values-{freq}.txt"),
                freq,
                self.area,
                self.link,
            )
            if self.mc_all:
                children[f"id-{freq}"] = LinkOutputSeriesMatrix(
                    self.context,
                    self.config.next_file(f"id-{freq}.txt"),
                    freq,
                    self.area,
                    self.link,
                )

        return {
            child: children[child]
            for child in children
            # this takes way too long... see above todo to prevent needing this
            # if cast(LinkOutputSeriesMatrix, children[child]).file_exists()
        }
