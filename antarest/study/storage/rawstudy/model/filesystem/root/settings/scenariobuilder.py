from typing import Dict, Type

from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode


class ScenarioBuilder(IniFileNode):
    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        self.config = config

        rules: Dict[str, Type[int]] = {}
        for area in self.config.areas:
            for mode in ["l", "s", "w", "h"]:
                rules[f"{mode},{area},0"] = int
            self._add_thermal(area, rules)

        super().__init__(
            context=context,
            config=config,
            types={"Default Ruleset": rules},
        )

    def _add_thermal(self, area: str, rules: Dict[str, Type[int]]) -> None:
        # Note that cluster IDs are case-insensitive, but series IDs are in lower case.
        # For instance, if your cluster ID is "Base", then the series ID will be "base".
        series_ids = map(str.lower, self.config.get_thermal_ids(area))
        for series_id in series_ids:
            rules[f"t,{area},0,{series_id}"] = int
