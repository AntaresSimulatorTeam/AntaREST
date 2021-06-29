from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.context import ContextServer
from antarest.storage.repository.filesystem.ini_file_node import IniFileNode


class BindingConstraintsIni(IniFileNode):
    def __init__(self, context: ContextServer, config: StudyConfig):
        IniFileNode.__init__(self, context, config, types={})
