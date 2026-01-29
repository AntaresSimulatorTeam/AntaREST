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
from io import StringIO
from pathlib import Path

import yaml
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

from antarest.core.persistence import upgrade_db


def test_alembic_migration(tmp_path: Path, project_path: Path) -> None:
    # Create a fake config file pointing towards the DB in memory

    db_file = tmp_path / "db.sqlite"
    db_url = f"sqlite:///{db_file}"

    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.safe_dump({"db": {"url": db_url}}, f)

    # This will fail if there's an issue inside our alembic migrations
    upgrade_db(config_file)

    engine = create_engine(db_url)
    with engine.connect() as connection:
        # this would throw if the migration is not executed
        connection.execute(text("SELECT * FROM study"))

    # If we have 2 heads with the same revision, we should raise to ensure a linear history
    # Before this part, if it was the case we didn't raise
    alembic_cfg = Config(str(project_path / "alembic.ini"))
    alembic_cfg.stdout = StringIO()
    command.heads(alembic_cfg)
    head_output = alembic_cfg.stdout.getvalue()
    heads = head_output.replace(' (head)', '').splitlines()
    if len(heads) > 1:
        raise AssertionError(f"We should have only one head, currently: {heads}")
