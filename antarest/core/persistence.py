# Copyright (c) 2025, RTE (https://www.rte-france.com)
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

import logging
import os
from io import StringIO
from pathlib import Path

from sqlalchemy.orm import declarative_base

from alembic import command
from alembic.config import Config
from alembic.util import CommandError
from antarest.core.utils.utils import get_local_path

logger = logging.getLogger(__name__)

Base = declarative_base()


def upgrade_db(config_file: Path) -> None:
    os.environ.setdefault("ANTAREST_CONF", str(config_file))
    alembic_cfg = Config(str(get_local_path() / "alembic.ini"))
    alembic_cfg.stdout = StringIO()
    alembic_cfg.set_main_option("script_location", str(get_local_path() / "alembic"))
    try:
        command.current(alembic_cfg)
        current_version_output = alembic_cfg.stdout.getvalue()
        current_version = current_version_output.strip()
    except CommandError as e:
        logger.error(
            "Failed to find current database version, make sure you use the latest version of the application",
            exc_info=e,
        )
        raise e

    alembic_cfg.stdout = StringIO()
    command.heads(alembic_cfg)  # type: ignore
    head_output = alembic_cfg.stdout.getvalue()
    head = head_output.split(" ")[0].strip()
    if current_version != head:
        logger.info(f"Upgrading database from {current_version} to {head}")
        command.upgrade(alembic_cfg, head)
    logger.info("Database up to date")
