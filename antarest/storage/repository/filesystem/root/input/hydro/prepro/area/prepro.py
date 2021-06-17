from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.context import ContextServer
from antarest.storage.repository.filesystem.ini_file_node import IniFileNode


class InputHydroPreproAreaPrepro(IniFileNode):
    def __init__(self, context: ContextServer, config: StudyConfig):
        types = {"prepro": {"intermonthly-correlation": float}}
        IniFileNode.__init__(self, context, config, types)
