from antarest.storage.repository.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.repository.filesystem.context import ContextServer
from antarest.storage.repository.filesystem.ini_file_node import IniFileNode


class InputHydroAllocationArea(IniFileNode):
    def __init__(
        self, context: ContextServer, config: FileStudyTreeConfig, area: str
    ):
        types = {"[allocation": {area: int}}
        IniFileNode.__init__(self, context, config, types)
