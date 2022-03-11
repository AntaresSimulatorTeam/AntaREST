from antarest.study.storage.rawstudy.io.reader import IniReader
from antarest.study.storage.rawstudy.io.writer.ini_writer import IniWriter
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import (
    IniFileNode,
    DEFAULT_INI_VALIDATOR,
)


class ExpansionCandidate(IniFileNode):
    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        super().__init__(context, config, validator=DEFAULT_INI_VALIDATOR)
