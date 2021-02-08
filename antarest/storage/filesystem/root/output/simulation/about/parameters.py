from antarest.storage.filesystem.config.model import StudyConfig
from antarest.storage.filesystem.ini_file_node import IniFileNode
from antarest.storage.filesystem.root.settings.generaldata import (
    GeneralData,
)


class OutputSimulationAboutParameters(IniFileNode):
    def __init__(self, config: StudyConfig):
        IniFileNode.__init__(self, config, GeneralData.TYPES)
