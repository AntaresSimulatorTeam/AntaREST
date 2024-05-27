import logging
import typing as t
from typing import Optional, List

from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode

logger = logging.getLogger(__name__)


class ScenarioUtils:
    SCENARIOS = [
        {"type": "load", "symbol": "l"},
        {"type": "thermal", "symbol": "t"},
        {"type": "hydro", "symbol": "h"},
        {"type": "wind", "symbol": "w"},
        {"type": "solar", "symbol": "s"},
        {"type": "ntc", "symbol": "ntc"},
        {"type": "renewable", "symbol": "r"},
        {"type": "bindingConstraints", "symbol": "bc"},
    ]

    TYPES_BY_SYMBOL = {scenario["type"]: scenario["symbol"] for scenario in SCENARIOS}
    SYMBOLS_BY_TYPE = {scenario["symbol"]: scenario["type"] for scenario in SCENARIOS}

    @staticmethod
    def parse_line(line: str) -> t.Tuple[Optional[str], Optional[int]]:
        line = line.strip()
        if line.startswith("[") and line.endswith("]"):
            return line[1:-1], None
        if "=" in line:
            key, value = line.split("=", 1)
            key = key.strip()
            try:
                value = int(value.strip())
                return key, value
            except ValueError:
                logger.warning(
                    f"Invalid scenario configuration value detected for key '{key}': '{value}' is not a valid integer."
                )
        return None, None

    @staticmethod
    def extract_url_params(url: Optional[List[str]]) -> t.Tuple[str, Optional[str]]:
        """
        Extracts and returns the active ruleset and scenario type from the URL parameters.

        :param url: URL parameters list
        :return: Tuple containing active ruleset and scenario type
        """
        if url:
            active_ruleset = url[0]
            scenario_type = None if not url[1] or url[1] == "None" else url[1]
        else:
            active_ruleset = "Default Ruleset"
            scenario_type = None
        return active_ruleset, scenario_type


class ScenarioBuilder(IniFileNode):
    """
    Node representing the `settings/scenariobuilder.dat` file in an Antares study.
    This ".dat" file is a kind of ".ini"" file, where sections are rulesets.
    Each ruleset is a set of rules defined for each kind of generator or link.
    | Label                  | Symbol | Format                                     | Availability |
    |------------------------|:------:|--------------------------------------------|:------------:|
    | load                   |   l    | `l,<area>,<year> = <TS number>`            |              |
    | thermal                |   t    | `t,<area>,<year>,<cluster> = <TS number>`  |              |
    | hydro                  |   h    | `h,<area>,<year> = <TS number>`            |              |
    | wind                   |   w    | `w,<area>,<year> = <TS number>`            |              |
    | solar                  |   s    | `s,<area>,<year> = <TS number>`            |              |
    | NTC (links)            |  ntc   | `ntc,<area1>,<area2>,<year> = <TS number>` |              |
    | renewable              |   r    | `r,<area>,<year>,<cluster> = <TS number>`  |     8.1      |
    | binding-constraints    |   bc   | `bc,<group>,<year> = <TS number>`          |     8.7      |
    | hydro initial levels   |   hl   | `hl,<area>,<year> = <Level>`               |     8.0      |
    | hydro final levels     |  hfl   | `hfl,<area>,<year> = <Level>`              |     9.2      |
    | hydro generation power |  hgp   | `hgp,<area>,<year> = <TS number>`          |     9.1      |
    Legend:
    - `<area>`: The area ID (in lower case).
    - `<area1>`, `<area2>`: The area IDs of the two connected areas (source and target).
    - `<year>`: The year (0-based index) of the time series.
    - `<cluster>`: The ID of the thermal / renewable cluster (in lower case).
    - `<group>`: The ID of the binding constraint group (in lower case).
    - `<TS number>`: The time series number (1-based index of the matrix column).
    - `<Level>`: The level of the hydraulic reservoir (in range 0-1).
    """

    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        rules: t.Dict[str, t.Union[t.Type[int], t.Type[float]]] = {}

        super().__init__(context=context, config=config, types={"Default Ruleset": rules})

    def _get(
        self, url: Optional[List[str]] = None, depth: int = -1, expanded: bool = False, get_node: bool = False
    ) -> dict:
        file_path = self.path
        current_section = None
        config_data = {}
        matched_symbol = False  # Flag to track the first occurrence of the scenario type.

        active_ruleset, scenario_type = ScenarioUtils.extract_url_params(url)
        symbol = ScenarioUtils.TYPES_BY_SYMBOL.get(scenario_type)

        with open(file_path, mode="r", encoding="utf-8") as file:
            for line in file:
                key, value = ScenarioUtils.parse_line(line)
                if key and value is None:
                    current_section = key
                    if current_section == active_ruleset:
                        config_data[current_section] = {}
                elif key and value is not None and current_section == active_ruleset:
                    if symbol:
                        if key.startswith(symbol):
                            matched_symbol = True
                            config_data[current_section][key] = value
                        elif matched_symbol:
                            break
                    else:
                        config_data[current_section][key] = value
        return config_data
