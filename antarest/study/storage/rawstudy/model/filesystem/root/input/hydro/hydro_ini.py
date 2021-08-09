from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import (
    IniFileNode,
)


class InputHydroIni(IniFileNode):
    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        sections = [
            "inter-daily-breakdown",
            "intra-daily-modulation",
            "inter-monthly-breakdown",
        ]
        if config.version >= 650:
            sections += [
                "initialize reservoir date",
                "leeway low",
                "leeway up",
                "pumping efficiency",
            ]
        section = {a: (int, float) for a in config.area_names()}
        types = {name: section for name in sections}

        IniFileNode.__init__(self, context, config, types)
