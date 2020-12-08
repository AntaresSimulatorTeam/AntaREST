from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.ini_file_node import IniFileNode


class InputThermalAreaIni(IniFileNode):
    def __init__(self, config: Config):
        section = {a: float for a in config.area_names}
        types = {"unserverdenergycost": section, "spilledenergycost": {}}
        IniFileNode.__init__(self, config, types)
