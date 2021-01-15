from api_iso_antares.filesystem.config.model import Config
from api_iso_antares.filesystem.ini_file_node import IniFileNode


class InputThermalAreasIni(IniFileNode):
    def __init__(self, config: Config):
        section = {a: float for a in config.area_names()}
        types = {"unserverdenergycost": section, "spilledenergycost": {}}
        IniFileNode.__init__(self, config, types)
