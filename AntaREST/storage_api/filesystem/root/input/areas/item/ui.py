from AntaREST.storage_api.filesystem.config.model import Config
from AntaREST.storage_api.filesystem.ini_file_node import IniFileNode


class InputAreasUi(IniFileNode):
    """
    Examples
    --------
    [ui]
    x = 1
    y = 135
    color_r = 0
    color_g = 128
    color_b = 255
    layers = 0
    [layerX]
    0 = 1

    [layerY]
    0 = 135

    [layerColor]
    0 = 0 , 128 , 255
    """

    def __init__(self, config: Config):
        types = {
            "ui": {
                "x": int,
                "y": int,
                "color_r": int,
                "color_g": int,
                "color_b": int,
                "layers": int,
            },
            "layerX": {"0": int},
            "layerY": {"0": int},
            "layerColor": {"0": str},
        }
        IniFileNode.__init__(self, config, types)
