from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import (
    IniFileNode,
    DEFAULT_INI_VALIDATOR,
)


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

    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        types = {
            "layers": {},
            "activeLayer": {"activeLayerID": int, "showAllLayer": bool},
        }
        IniFileNode.__init__(
            self, context, config, validator=DEFAULT_INI_VALIDATOR
        )
