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

from pathlib import Path

import yaml
from sqlalchemy import create_engine, text
from testcontainers.postgres import PostgresContainer

from antarest.core.persistence import upgrade_db


def _checks_migration(tmp_path: Path, db_url: str) -> None:
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.safe_dump({"db": {"url": db_url}}, f)

    # This will fail if there's an issue inside our alembic migrations
    upgrade_db(config_file)

    engine = create_engine(db_url)
    with engine.connect() as connection:
        # this would throw if the migration is not executed
        connection.execute(text("SELECT * FROM study"))


def test_alembic_migration(tmp_path: Path) -> None:
    # Create a fake config file pointing towards the DB in memory
    db_file = tmp_path / "db.sqlite"
    db_url = f"sqlite:///{db_file}"

    _checks_migration(tmp_path, db_url)


def test_alembic_migration_postgresql(tmp_path: Path) -> None:
    # Start a PostgreSQL container
    with PostgresContainer("postgres:15") as postgres:
        db_url = postgres.get_connection_url()

        _checks_migration(tmp_path, db_url)
