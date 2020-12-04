from typing import Dict

from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.ini_file_node import IniFileNode


class ScenarioBuilder(IniFileNode):
    def __init__(self, config: Config):
        self.config = config

        rules = dict()
        for area in self.config.areas:
            for mode in ["l", "s", "w", "h"]:
                rules[f"{mode},{area},0"] = int
            self._add_thermal(area, rules)

        IniFileNode.__init__(
            self, config=config, types={"Default Ruleset": rules}
        )

    def _add_thermal(self, area: str, rules: Dict):
        for thermal in self.config.get_thermals(area):
            rules[f"t,{area},0,{thermal}"] = int
