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

from sqlalchemy.orm import DeclarativeBase

from alembic import command
from alembic.config import Config
from alembic.util import CommandError

from antarest.core.persistence import upgrade_db
from antarest.core.utils.utils import get_local_path


def test_alembic_migration(tmp_path: Path) -> None:
    # Create a fake config file pointing towards the DB in memory
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
"""db:
  url: "sqlite:///memory"
""")
    try:
        # This will fail if there's an issue inside our alembic migrations
        upgrade_db(config_file)
    finally:
        # Remove the created DB
        db_path = Path(__file__).parent.parent.parent / "memory"
        db_path.unlink(missing_ok=True)
