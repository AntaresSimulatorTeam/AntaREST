from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.ini_file_node import IniFileNode


class InputWindPreproAreaSettings(IniFileNode):
    def __init__(self, config: Config):
        IniFileNode.__init__(self, config, types={})
