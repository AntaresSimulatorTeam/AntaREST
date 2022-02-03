from antarest.study.storage.rawstudy.model.filesystem.bucket_node import (
    BucketNode,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.root.user.expansion.expansion import (
    Expansion,
)


class User(BucketNode):
    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        planned_files = {"expansion": Expansion}
        super().__init__(context, config, planned_files)
