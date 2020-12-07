from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.ini_file_node import IniFileNode


class InputHydroAllocationArea(IniFileNode):
    def __init__(self, config: Config, area: str):
        types = {"[allocation": {area: int}}
        IniFileNode.__init__(self, config, types)
