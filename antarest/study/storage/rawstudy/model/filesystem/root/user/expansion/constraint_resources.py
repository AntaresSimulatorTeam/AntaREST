from antarest.study.storage.rawstudy.model.filesystem.bucket_node import (
    BucketNode,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)


class ExpansionConstraintResources(BucketNode):
    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        super().__init__(context, config, None)
