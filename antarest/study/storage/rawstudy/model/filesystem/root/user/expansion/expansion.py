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
from antarest.study.storage.rawstudy.model.filesystem.root.user.expansion.capa import (
    ExpansionCapa,
)
from antarest.study.storage.rawstudy.model.filesystem.root.user.expansion.settings import (
    ExpansionSettings,
)


class Expansion(BucketNode):
    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        registered_files = {
            "candidates": RegisteredFile(
                ExpansionCandidates, extension=".ini"
            ),
            "settings": RegisteredFile(ExpansionSettings, extension=".ini"),
            "capa": RegisteredFile(ExpansionCapa),
        }
        super().__init__(context, config, registered_files)
