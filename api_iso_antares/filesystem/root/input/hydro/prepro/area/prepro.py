from api_iso_antares.filesystem.config.model import Config
from api_iso_antares.filesystem.ini_file_node import IniFileNode


class InputHydroPreproAreaPrepro(IniFileNode):
    def __init__(self, config: Config):
        types = {"prepro": {"intermonthly-correlation": float}}
        IniFileNode.__init__(self, config, types)
