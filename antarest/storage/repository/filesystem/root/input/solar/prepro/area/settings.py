from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.ini_file_node import IniFileNode


class InputSolarPreproAreaSettings(IniFileNode):
    def __init__(self, config: StudyConfig):
        IniFileNode.__init__(self, config, types={})
