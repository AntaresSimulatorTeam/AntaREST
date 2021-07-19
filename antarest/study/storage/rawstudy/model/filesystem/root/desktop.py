from antarest.storage.business.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.business.rawstudy.model.filesystem.context import ContextServer
from antarest.storage.business.rawstudy.model.filesystem.ini_file_node import IniFileNode


class Desktop(IniFileNode):
    """
    Desktop.ini file

    Examples
    --------
    [.shellclassinfo]
    iconfile = settings/resources/study.ico
    iconindex = 0
    infotip = Antares Study7.0: STA-mini
    """

    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        types = {
            ".shellclassinfo": {
                "iconfile": str,
                "iconindex": int,
                "infotip": str,
            }
        }

        IniFileNode.__init__(self, context, config, types=types)
