import numpy as np

# Matrice shapes for binding constraints are different from usual shapes,
# because we need to take leap years into account, which contains 366 days and 8784 hours.
# Also, we use the same matrices for "weekly" and "daily" frequencies,
# because the solver calculates the weekly matrix from the daily matrix.
# See https://github.com/AntaresSimulatorTeam/AntaREST/issues/1843

default_bc_hourly = np.zeros((8784, 3), dtype=np.float64)
default_bc_hourly.flags.writeable = False

default_bc_weekly_daily = np.zeros((366, 3), dtype=np.float64)
default_bc_weekly_daily.flags.writeable = False
