from enum import Enum


class FilteringOptions(Enum):
    FILTER_SYNTHESIS: str = "hourly, daily, weekly, monthly, annual"
    FILTER_YEAR_BY_YEAR: str = "hourly, daily, weekly, monthly, annual"


class NodalOptimization(Enum):
    NON_DISPATCHABLE_POWER: str = "true"
    DISPATCHABLE_HYDRO_POWER: str = "true"
    OTHER_DISPATCHABLE_POWER: str = "true"
    SPREAD_UNSUPPLIED_ENERGY_COST: float = 0.000000
    SPREAD_SPILLED_ENERGY_COST: float = 0.000000
    UNSERVERDDENERGYCOST: float = 0.000000
    SPILLEDENERGYCOST: float = 0.000000
