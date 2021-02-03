from antarest.storage_api.filesystem.config.model import StudyConfig
from antarest.storage_api.filesystem.ini_file_node import IniFileNode


class InputSolarPreproCorrelation(IniFileNode):
    def __init__(self, config: StudyConfig):
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
