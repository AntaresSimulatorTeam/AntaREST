from api_iso_antares.filesystem.config.model import Config
from api_iso_antares.filesystem.ini_file_node import IniFileNode
from api_iso_antares.filesystem.root.settings.generaldata import GeneralData


class OutputSimulationAboutParameters(IniFileNode):
    def __init__(self, config: Config):
        IniFileNode.__init__(self, config, GeneralData.TYPES)
