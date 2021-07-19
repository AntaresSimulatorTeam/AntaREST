from antarest.storage.business.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.business.rawstudy.model.filesystem.context import ContextServer
from antarest.storage.business.rawstudy.model.filesystem.ini_file_node import IniFileNode


class InputThermalAreasIni(IniFileNode):
    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        section = {a: float for a in config.area_names()}
        types = {"unserverdenergycost": section, "spilledenergycost": {}}
        IniFileNode.__init__(self, context, config, types)
