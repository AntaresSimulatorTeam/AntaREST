# Copyright (c) 2024, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import os
from pathlib import Path

from antarest.main import fastapi_app


def get_env_var(env_var_name: str) -> str:
    env_var = os.getenv(env_var_name)
    if env_var is None:
        raise EnvironmentError(f"API need the env var: {env_var_name}.")
    return env_var


env_var_conf_path = get_env_var("ANTAREST_CONF")
conf_path = Path(env_var_conf_path)

app, _ = fastapi_app(conf_path, mount_front=False)
