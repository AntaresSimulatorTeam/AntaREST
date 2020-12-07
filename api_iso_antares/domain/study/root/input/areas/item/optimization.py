from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.ini_file_node import IniFileNode


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

    def __init__(self, config: Config):
        types = {
            "nodal optimization": {
                "non-dispatchable-power": bool,
                "dispatchable-hydro-power": bool,
                "other-dispatchable-power": bool,
                "spread-unsupplied-energy-cost": float,
                "spread-spilled-energy-cost": float,
            },
            "filtering": {"filter-synthesis": str, "filter-year-by-year": str},
        }
        IniFileNode.__init__(self, config, types)
