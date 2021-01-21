from storage_api.filesystem.config.model import Config
from storage_api.filesystem.ini_file_node import IniFileNode


class LayersIni(IniFileNode):
    """
    Examples
    -------
    [layers]
    0 = All
    1 = Map 1
    [activeLayer]
    activeLayerID = 0
    showAllLayer = true
    """

    def __init__(self, config: Config):
        types = {
            "layers": {},
            "activeLayer": {"activeLayerID": int, "showAllLayer": bool},
        }
        IniFileNode.__init__(self, config, types=types)
