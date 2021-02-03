from antarest.storage_api.filesystem.config.model import StudyConfig
from antarest.storage_api.filesystem.ini_file_node import IniFileNode


class OutputSimulationAboutStudy(IniFileNode):
    def __init__(self, config: StudyConfig):
        types = {
            "antares": {
                "version": int,
                "caption": str,
                "created": int,
                "lastsave": int,
                "author": str,
            }
        }
        IniFileNode.__init__(self, config, types)
