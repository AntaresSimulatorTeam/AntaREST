from jsonschema import Draft7Validator

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


class InputAreasOptimization(IniFileNode):
    """
    Examples
    --------

    [nodal optimization]
    non-dispatchable-power = true
    dispatchable-hydro-power = true
    other-dispatchable-power = true
    spread-unsupplied-energy-cost = 0.000000
    spread-spilled-energy-cost = 0.000000

    [filtering]
    filter-synthesis = daily, monthly
    filter-year-by-year = hourly, weekly, annual
    """

    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        base_schema = {
            "type": "object",
            "properties": {
                "nodal optimization": {
                    "type": "object",
                    "properties": {
                        "non-dispatchable-power": {"type": "boolean"},
                        "dispatchable-hydro-power": {"type": "boolean"},
                        "other-dispatchable-power": {"type": "boolean"},
                        "spread-unsupplied-energy-cost": {
                            "type": "number",
                        },
                        "spread-spilled-energy-cost": {
                            "type": "number",
                        },
                        "additionalProperties": False,
                    },
                },
                "filtering": {
                    "type": "object",
                    "properties": {
                        "filter-synthesis": {"type": "string"},
                        "filter-year-by-year": {"type": "string"},
                    },
                    "additionalProperties": False,
                },
                "additionalProperties": False,
            },
        }
        IniFileNode.__init__(
            self, context, config, validator=Draft7Validator(base_schema)
        )
