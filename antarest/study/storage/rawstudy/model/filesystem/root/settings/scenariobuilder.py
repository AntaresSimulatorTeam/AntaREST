import typing as t
from typing import Dict, Type, Optional, List

from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode

scenario_symbols = {
    "load": "l",
    "thermal": "t",
    "hydro": "h",
    "wind": "w",
    "solar": "s",
    "ntc": "ntc",
    "renewable": "r",
    "bindingConstraints": "bc",
}


def parse_line(line: str):
    line = line.strip()
    if line.startswith('[') and line.endswith(']'):
        # This is a section header
        return line[1:-1], None  # Returns section name and None for value
    if '=' in line:
        key, value = line.split('=', 1)
        key = key.strip()
        try:
            value = int(value.strip())
            return key, value
        except ValueError:
            print(f"Invalid configuration value detected for key '{key}': '{value}' is not a valid integer.")
    return None, None


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

    def _get(self, url: Optional[List[str]] = None, depth: int = -1, expanded: bool = False, get_node: bool = False):

        file_path = self.path
        current_section = None
        data = {}

        matched_symbol = False  # Flag to track the first occurrence of the scenario type.

        if url:
            # The URL list includes essential filtering criteria: [active_ruleset, scenario_type].
            # active_ruleset: Defines which configuration ruleset to apply.
            # scenario_type: Specifies the type of scenario to filter configuration data by, if applicable.
            active_ruleset = url[0]  # Retrieve the active ruleset identifier from the URL.
            # Convert 'None' or empty string to None for scenario_type to ensure proper filtering.
            scenario_type = None if not url[1] or url[1] == 'None' else url[1]
        else:
            # Defaults are used if no URL parameters are provided.
            active_ruleset = 'Default Ruleset'  # Default ruleset if none specified.
            scenario_type = None  # No scenario filtering if not specified.

        symbol = None if not scenario_type else scenario_symbols[scenario_type]

        with open(file_path, mode='r', encoding='utf-8') as file:
            for line in file:
                key, value = parse_line(line)
                if key and value is None:
                    # Detect new configuration sections (e.g., [Ruleset B]).
                    current_section = key
                    if current_section == active_ruleset:
                        data[current_section] = {}
                elif key and value is not None and current_section == active_ruleset:
                    # Check if the key matches the active ruleset and scenario type.
                    if symbol:
                        if key.startswith(symbol):
                            if not matched_symbol:
                                matched_symbol = True  # Mark the first match of the scenario type.
                            data[current_section][key] = value
                        elif matched_symbol:
                            # If a different scenario type is encountered after the first match, stop processing.
                            break
                    else:
                        # If no specific scenario type is provided, all entries under the current section are included.
                        data[current_section][key] = value
        return data
