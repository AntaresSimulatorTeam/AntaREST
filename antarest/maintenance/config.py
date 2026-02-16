# Copyright (c) 2026, RTE (https://www.rte-france.com)
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
"""
This module is used to load the antares configuration for the celery app.

It's located outside from the celery app module to enable monkey-patching for testing.
"""

import os
from pathlib import Path

from antarest.core.config import Config
from antarest.core.exceptions import ConfigurationError
from antarest.core.utils.utils import get_local_path

_config: Config | None = None


def load_config() -> None:
    """
    Load config from ANTAREST_CONF env var, else raises.

    In practice, this will abort celery app startup, since it's called at the app module level.
    """
    config_path_str = os.environ.get("ANTAREST_CONF")

    if not config_path_str or not Path(config_path_str).exists():
        raise ConfigurationError(
            "You must provide a path to the YAML configuration file through the ANTAREST_CONF env variable the to "
            "start celery app."
        )
    config_path = Path(config_path_str)
    res = get_local_path() / "resources"
    global _config
    _config = Config.from_yaml_file(res=res, file=config_path)


def get_config() -> Config:
    if not _config:
        raise ConfigurationError("Application config not loaded.")
    return _config
