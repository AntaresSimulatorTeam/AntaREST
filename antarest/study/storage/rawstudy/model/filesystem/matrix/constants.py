import numpy as np

default_scenario_hourly = np.zeros((8760, 1), dtype=np.float64)
default_scenario_hourly.flags.writeable = False

default_scenario_daily = np.zeros((365, 1), dtype=np.float64)
default_scenario_daily.flags.writeable = False

default_scenario_monthly = np.zeros((12, 1), dtype=np.float64)
default_scenario_monthly.flags.writeable = False

default_4_fixed_hourly = np.zeros((8760, 4), dtype=np.float64)
default_4_fixed_hourly.flags.writeable = False

default_8_fixed_hourly = np.zeros((8760, 8), dtype=np.float64)
default_8_fixed_hourly.flags.writeable = False

default_binding_constraint_hourly = np.zeros((8760, 3), dtype=np.float64)
default_binding_constraint_hourly.flags.writeable = False

default_binding_constraint_daily = np.zeros((365, 3), dtype=np.float64)
default_binding_constraint_daily.flags.writeable = False

default_binding_constraint_weekly = np.zeros((52, 3), dtype=np.float64)
default_binding_constraint_weekly.flags.writeable = False
