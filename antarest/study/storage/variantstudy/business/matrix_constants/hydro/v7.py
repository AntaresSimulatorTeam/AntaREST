from antarest.matrixstore.model import MatrixContent

credit_modulations = MatrixContent(data=[[1] * 101] * 2)
inflow_pattern = MatrixContent(data=[[1]] * 365)
max_power = MatrixContent(data=[[0, 24, 0, 24]] * 365)
reservoir = MatrixContent(data=[[0, 0.5, 1]] * 365)
