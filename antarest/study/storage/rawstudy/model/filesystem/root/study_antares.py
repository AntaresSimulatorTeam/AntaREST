from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import (
    IniFileNode,
)


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

    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        types = {
            "antares": {
                "version": int,
                "caption": str,
                "created": int,
                "lastsave": int,
                "author": str,
            }
        }
        IniFileNode.__init__(self, context, config, types=types)
