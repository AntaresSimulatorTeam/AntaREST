from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.ini_file_node import IniFileNode


class InputThermalAreasIni(IniFileNode):
    def __init__(self, config: StudyConfig):
        section = {a: float for a in config.area_names()}
        types = {"unserverdenergycost": section, "spilledenergycost": {}}
        IniFileNode.__init__(self, config, types)
