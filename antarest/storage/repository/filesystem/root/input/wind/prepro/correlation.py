from antarest.storage.repository.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.repository.filesystem.context import ContextServer
from antarest.storage.repository.filesystem.ini_file_node import IniFileNode


class InputWindPreproCorrelation(IniFileNode):
    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        types = {
            "general": {"mode": str},
            "0": {},
            "1": {},
            "2": {},
            "3": {},
            "4": {},
            "5": {},
            "6": {},
            "7": {},
            "8": {},
            "9": {},
            "10": {},
            "11": {},
        }
        IniFileNode.__init__(self, context, config, types)
