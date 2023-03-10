from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import (
    MatrixFrequency,
)
from antarest.study.storage.rawstudy.model.filesystem.matrix.output_series_matrix import (
    BindingConstraintOutputSeriesMatrix,
)


class OutputSimulationBindingConstraintItem(FolderNode):
    def build(self) -> TREE:
        # filters = self.config.get_filters_synthesis(self.area, self.link)
        # todo get the config related to this output (now this may fail if input has changed since the launch)

        freq: MatrixFrequency
        children: TREE = {
            f"binding-constraints-{freq}": BindingConstraintOutputSeriesMatrix(
                self.context,
                self.config.next_file(f"binding-constraints-{freq}.txt"),
                freq,
            )
            for freq in MatrixFrequency
        }
        return {
            child: children[child]
            for child in children
            # this takes way too long... see above todo to prevent needing this
            # if cast(LinkOutputSeriesMatrix, children[child]).file_exists()
        }
