from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.ini_file_node import IniFileNode


class OutputSimulationAboutStudy(IniFileNode):
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
        IniFileNode.__init__(self, config, types)
