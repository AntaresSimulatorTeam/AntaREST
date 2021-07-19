from antarest.storage.business.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.business.rawstudy.model.filesystem.context import ContextServer
from antarest.storage.business.rawstudy.model.filesystem.ini_file_node import IniFileNode


class InputHydroPreproAreaPrepro(IniFileNode):
    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        types = {"prepro": {"intermonthly-correlation": float}}
        IniFileNode.__init__(self, context, config, types)
