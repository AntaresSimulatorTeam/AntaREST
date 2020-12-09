from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.ini_file_node import IniFileNode


class StudyAntares(IniFileNode):
    """
    study.antares files

    Examples
    --------
    [antares]
    version = 700
    caption = STA-mini
    created = 1480683452
    lastsave = 1602678639
    author = Andrea SGATTONI

    """

    def __init__(self, config: Config):
        types = {
            "antares": {
                "version": int,
                "caption": str,
                "created": int,
                "lastsave": int,
                "author": str,
            }
        }
        IniFileNode.__init__(self, config, types=types)
