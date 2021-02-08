from typing import Dict, Type

from antarest.storage.filesystem.config.model import StudyConfig
from antarest.storage.filesystem.ini_file_node import IniFileNode


class ScenarioBuilder(IniFileNode):
    def __init__(self, config: StudyConfig):
        self.config = config

        rules: Dict[str, Type[int]] = dict()
        for area in self.config.areas:
            for mode in ["l", "s", "w", "h"]:
                rules[f"{mode},{area},0"] = int
            self._add_thermal(area, rules)

        IniFileNode.__init__(
            self, config=config, types={"Default Ruleset": rules}
        )

    def _add_thermal(self, area: str, rules: Dict[str, Type[int]]) -> None:
        for thermal in self.config.get_thermals(area):
            rules[f"t,{area},0,{thermal}"] = int
