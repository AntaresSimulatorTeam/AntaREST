from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.ini_file_node import IniFileNode


class InputLoadPreproCorrelation(IniFileNode):
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
