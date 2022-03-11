from antarest.study.storage.rawstudy.model.filesystem.bucket_node import (
    BucketNode,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import (
    InputSeriesMatrix,
)


class ExpansionCapa(BucketNode):
    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        super().__init__(
            context, config, None, default_file_node=InputSeriesMatrix
        )
