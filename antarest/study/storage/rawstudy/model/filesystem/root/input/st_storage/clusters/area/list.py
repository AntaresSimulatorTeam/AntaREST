from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import (
    IniFileNode,
)


class InputShortTermStorageAreaList(IniFileNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        area: str,
    ):
        types = {
            st_storage: dict
            for st_storage in config.get_short_term_storage_names(area)
        }
        IniFileNode.__init__(self, context, config, types)
