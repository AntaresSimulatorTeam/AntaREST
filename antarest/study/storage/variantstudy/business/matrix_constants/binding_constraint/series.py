import numpy as np

default_binding_constraint_hourly = np.zeros((8760, 3), dtype=np.float64)
default_binding_constraint_hourly.flags.writeable = False

default_binding_constraint_daily = np.zeros((365, 3), dtype=np.float64)
default_binding_constraint_daily.flags.writeable = False

default_binding_constraint_weekly = np.zeros((52, 3), dtype=np.float64)
default_binding_constraint_weekly.flags.writeable = False
