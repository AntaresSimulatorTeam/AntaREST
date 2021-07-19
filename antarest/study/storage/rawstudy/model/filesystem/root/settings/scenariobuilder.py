from typing import Dict, Type

from antarest.storage.business.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.business.rawstudy.model.filesystem.context import ContextServer
from antarest.storage.business.rawstudy.model.filesystem.ini_file_node import IniFileNode


class ScenarioBuilder(IniFileNode):
    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        self.config = config

        rules: Dict[str, Type[int]] = dict()
        for area in self.config.areas:
            for mode in ["l", "s", "w", "h"]:
                rules[f"{mode},{area},0"] = int
            self._add_thermal(area, rules)

        IniFileNode.__init__(
            self,
            context=context,
            config=config,
            types={"Default Ruleset": rules},
        )

    def _add_thermal(self, area: str, rules: Dict[str, Type[int]]) -> None:
        for thermal in self.config.get_thermal_names(area):
            rules[f"t,{area},0,{thermal}"] = int
