from antarest.storage.filesystem.config.model import StudyConfig
from antarest.storage.filesystem.ini_file_node import IniFileNode


class InputHydroIni(IniFileNode):
    def __init__(self, config: StudyConfig):
        sections = [
            "inter-daily-breakdown",
            "intra-daily-modulation",
            "inter-monthly-breakdown",
            "initialize reservoir date",
            "leeway low",
            "leeway up",
            "pumping efficiency",
        ]
        section = {a: (int, float) for a in config.area_names()}
        types = {name: section for name in sections}

        IniFileNode.__init__(self, config, types)
