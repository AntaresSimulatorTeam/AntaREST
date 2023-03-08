from enum import Enum

default_scenario_hourly = [[0.0]] * 8760
default_scenario_daily = [[0.0]] * 365
default_scenario_monthly = [[0.0]] * 12
default_4_fixed_hourly = [[0.0, 0.0, 0.0, 0.0]] * 8760
default_8_fixed_hourly = [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]] * 8760


class MatrixFrequency(str, Enum):
    ANNUAL = "annual"
    MONTHLY = "monthly"
    WEEKLY = "weekly"
    DAILY = "daily"
    HOURLY = "hourly"
