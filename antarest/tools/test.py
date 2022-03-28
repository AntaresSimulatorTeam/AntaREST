from pathlib import Path

config_file = Path(
    "/home/buiquangpau/projects/antares/_antares_config/application-local.yaml"
)
from antarest.main import create_env

services = create_env(config_file)
bjm = services["launcher"].launchers["slurm"].batch_jobs
mc_alls = bjm.reconstruct_synthesis(
    Path(
        "/home/buiquangpau/scratch/antares_workspace_internal/8e4e8916-348b-4949-bd2c-8109fe5a75aa"
    ),
    "20220325-1603eco",
    {2: 5, 3: 1},
)

# from pathlib import Path
# from antarest.tools import test
# import numpy as np
# import pandas as pd
#
# data = test.mc_alls
