from antarest.storage.repository.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.repository.filesystem.context import ContextServer
from antarest.storage.repository.filesystem.ini_file_node import IniFileNode
from antarest.storage.repository.filesystem.root.settings.generaldata import (
    GeneralData,
)


class OutputSimulationAboutParameters(IniFileNode):
    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        IniFileNode.__init__(self, context, config, GeneralData.TYPES)
