from antarest.study.storage.rawstudy.model.filesystem.bucket_node import (
    BucketNode,
    RegisteredFile,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.root.user.expansion.candidates import (
    ExpansionCandidates,
)
from antarest.study.storage.rawstudy.model.filesystem.root.user.expansion.constraint_resources import (
    ExpansionConstraintResources,
)
from antarest.study.storage.rawstudy.model.filesystem.root.user.expansion.matrix_resources import (
    ExpansionMatrixResources,
)
from antarest.study.storage.rawstudy.model.filesystem.root.user.expansion.settings import (
    ExpansionSettings,
)


class Expansion(BucketNode):
    registered_files = [
        RegisteredFile(
            key="candidates",
            node=ExpansionCandidates,
            filename="candidates.ini",
        ),
        RegisteredFile(
            key="settings", node=ExpansionSettings, filename="settings.ini"
        ),
        RegisteredFile(key="capa", node=ExpansionMatrixResources),
        RegisteredFile(key="weights", node=ExpansionMatrixResources),
        RegisteredFile(key="constraints", node=ExpansionConstraintResources),
    ]

    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        super().__init__(context, config, self.registered_files)
