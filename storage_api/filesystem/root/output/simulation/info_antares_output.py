from storage_api.filesystem.config.model import Config
from storage_api.filesystem.ini_file_node import IniFileNode


class OutputSimulationInfoAntaresOutput(IniFileNode):
    """
    info.antares-output file

    Examples
    --------
    [general]
    version = 700
    name = hello
    mode = Economy
    date = 2020.10.14 - 14:22
    title = 2020.10.14 - 14:22
    timestamp = 1602678140
    """

    def __init__(self, config: Config):
        types = {
            "general": {
                "version": int,
                "name": str,
                "mode": str,
                "date": str,
                "title": str,
                "timestamp": int,
            }
        }

        IniFileNode.__init__(self, config, types=types)
