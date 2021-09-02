from enum import Enum


class FilteringOptions(Enum):
    FILTER_SYNTHESIS: str = "hourly, daily, weekly, monthly, annual"
    FILTER_YEAR_BY_YEAR: str = "hourly, daily, weekly, monthly, annual"


class NodalOptimization(Enum):
    NON_DISPATCHABLE_POWER: str = "true"
    DISPATCHABLE_HYDRO_POWER: str = "true"
    OTHER_DISPATCHABLE_POWER: str = "true"
    SPREAD_UNSUPPLIED_ENERGY_COST: int = 0
    SPREAD_SPILLED_ENERGY_COST: int = 0
    UNSERVERDDENERGYCOST: int = 0
    SPILLEDENERGYCOST: int = 0


class LinkProperties(Enum):
    HURDLES_COST: str = "false"
    LOOP_FLOW: str = "false"
    USE_PHASE_SHIFTER: str = "false"
    TRANSMISSION_CAPACITIES: str = "enabled"
    ASSET_TYPE: str = "ac"
    LINK_STYLE: str = "plain"
    LINK_WIDTH: int = 1
    COLORR: int = 112
    COLORG: int = 112
    COLORB: int = 112
    DISPLAY_COMMENTS: str = "true"
