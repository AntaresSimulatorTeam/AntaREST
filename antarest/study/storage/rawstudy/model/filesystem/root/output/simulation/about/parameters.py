from antarest.storage.business.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.business.rawstudy.model.filesystem.context import ContextServer
from antarest.storage.business.rawstudy.model.filesystem.ini_file_node import IniFileNode
from antarest.storage.business.rawstudy.model.filesystem.root.settings.generaldata import (
    GeneralData,
)


class OutputSimulationAboutParameters(IniFileNode):
    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        IniFileNode.__init__(self, context, config, GeneralData.TYPES)
