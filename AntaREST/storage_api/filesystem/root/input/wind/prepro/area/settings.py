from AntaREST.storage_api.filesystem.config.model import Config
from AntaREST.storage_api.filesystem.ini_file_node import IniFileNode


class InputWindPreproAreaSettings(IniFileNode):
    def __init__(self, config: Config):
        IniFileNode.__init__(self, config, types={})
