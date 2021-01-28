from antarest.storage_api.filesystem.config.model import Config
from antarest.storage_api.filesystem.ini_file_node import IniFileNode


class InputHydroAllocationArea(IniFileNode):
    def __init__(self, config: Config, area: str):
        types = {"[allocation": {area: int}}
        IniFileNode.__init__(self, config, types)
