from storage_api.filesystem.config.model import Config
from storage_api.filesystem.ini_file_node import IniFileNode


class InputWindPreproCorrelation(IniFileNode):
    def __init__(self, config: Config):
        types = {
            "general": {"mode": str},
            "0": {},
            "1": {},
            "2": {},
            "3": {},
            "4": {},
            "5": {},
            "6": {},
            "7": {},
            "8": {},
            "9": {},
            "10": {},
            "11": {},
        }
        IniFileNode.__init__(self, config, types)
