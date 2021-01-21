from storage_api.filesystem.config.model import Config
from storage_api.filesystem.ini_file_node import IniFileNode


class InputLoadPreproAreaSettings(IniFileNode):
    def __init__(self, config: Config):
        IniFileNode.__init__(self, config, types={})
