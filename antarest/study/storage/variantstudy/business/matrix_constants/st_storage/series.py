import numpy as np

pmax_injection = np.ones((8760, 1), dtype=np.float64)
pmax_injection.flags.writeable = False
pmax_withdrawal = np.ones((8760, 1), dtype=np.float64)
pmax_withdrawal.flags.writeable = False
inflow = np.zeros((8760, 1), dtype=np.float64)
inflow.flags.writeable = False
lower_rule_curve = np.zeros((8760, 1), dtype=np.float64)
lower_rule_curve.flags.writeable = False
upper_rule_curve = np.ones((8760, 1), dtype=np.float64)
upper_rule_curve.flags.writeable = False
