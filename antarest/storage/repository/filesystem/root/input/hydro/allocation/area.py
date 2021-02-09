from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.ini_file_node import IniFileNode


class InputHydroAllocationArea(IniFileNode):
    def __init__(self, config: StudyConfig, area: str):
        types = {"[allocation": {area: int}}
        IniFileNode.__init__(self, config, types)
