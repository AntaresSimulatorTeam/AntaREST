from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.ini_file_node import IniFileNode


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

    def __init__(self, config: StudyConfig):
        types = {
            "layers": {},
            "activeLayer": {"activeLayerID": int, "showAllLayer": bool},
        }
        IniFileNode.__init__(self, config, types=types)
