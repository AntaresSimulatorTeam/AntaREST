from pathlib import Path

from antarest.storage.filesystem.config.model import StudyConfig
from antarest.storage.filesystem.ini_file_node import IniFileNode


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

    def __init__(self, config: StudyConfig):
        types = {
            ".shellclassinfo": {
                "iconfile": str,
                "iconindex": int,
                "infotip": str,
            }
        }

        IniFileNode.__init__(self, config, types=types)
