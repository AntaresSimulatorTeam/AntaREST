from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode


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
        types = {
            "nodal optimization": {
                "non-dispatchable-power": bool,
                "dispatchable-hydro-power": bool,
                "other-dispatchable-power": bool,
                "spread-unsupplied-energy-cost": (int, float),
                "spread-spilled-energy-cost": (int, float),
            },
            "filtering": {"filter-synthesis": str, "filter-year-by-year": str},
        }
        IniFileNode.__init__(self, context, config, types)
