from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import (
    IniFileNode,
)


class InputAreasAdequacyPatch(IniFileNode):
    # Examples
    # --------
    #
    # [adequacy-patch]
    #     adequacy-patch-mode = outside     # outside | inside | virtual
    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        types = {"adequacy-patch": {"adequacy-patch-mode": str}}
        IniFileNode.__init__(self, context, config, types)
