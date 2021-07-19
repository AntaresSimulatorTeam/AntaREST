from antarest.storage.repository.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.repository.filesystem.context import ContextServer
from antarest.storage.repository.filesystem.ini_file_node import IniFileNode


class OutputSimulationAboutStudy(IniFileNode):
    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        types = {
            "antares": {
                "version": int,
                "caption": str,
                "created": int,
                "lastsave": int,
                "author": str,
            }
        }
        IniFileNode.__init__(self, context, config, types)
