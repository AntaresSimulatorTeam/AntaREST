from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import (
    IniFileNode,
    DEFAULT_INI_VALIDATOR,
)


class InputThermalAreasIni(IniFileNode):
    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        section = {a: float for a in config.area_names()}
        types = {"unserverdenergycost": section, "spilledenergycost": {}}
        IniFileNode.__init__(
            self, context, config, validator=DEFAULT_INI_VALIDATOR
        )
