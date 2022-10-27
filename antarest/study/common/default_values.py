class FilteringOptions:
    FILTER_SYNTHESIS: str = "hourly, daily, weekly, monthly, annual"
    FILTER_YEAR_BY_YEAR: str = "hourly, daily, weekly, monthly, annual"


class NodalOptimization:
    NON_DISPATCHABLE_POWER: bool = True
    DISPATCHABLE_HYDRO_POWER: bool = True
    OTHER_DISPATCHABLE_POWER: bool = True
    SPREAD_UNSUPPLIED_ENERGY_COST: float = 0.000000
    SPREAD_SPILLED_ENERGY_COST: float = 0.000000
    UNSERVERDDENERGYCOST: float = 0.000000
    SPILLEDENERGYCOST: float = 0.000000


class LinkProperties:
    HURDLES_COST: bool = False
    LOOP_FLOW: bool = False
    USE_PHASE_SHIFTER: bool = False
    DISPLAY_COMMENTS: bool = True
    TRANSMISSION_CAPACITIES: str = "enabled"
    ASSET_TYPE: str = "ac"
    LINK_STYLE: str = "plain"
    LINK_WIDTH: int = 1
    COLORR: int = 112
    COLORG: int = 112
    COLORB: int = 112
