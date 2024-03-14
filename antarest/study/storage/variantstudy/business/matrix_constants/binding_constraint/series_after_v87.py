import numpy as np

default_bc_hourly = np.zeros((8784, 1), dtype=np.float64)
default_bc_hourly.flags.writeable = False

default_bc_weekly_daily = np.zeros((366, 1), dtype=np.float64)
default_bc_weekly_daily.flags.writeable = False
