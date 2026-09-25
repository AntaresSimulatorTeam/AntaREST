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

import pytest
import yaml
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from alembic import command
from antarest.core.utils.utils import get_local_path


def test_gems_catalog_migration_roundtrip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_url = f"sqlite:///{tmp_path / 'migration.sqlite'}"
    config_file = tmp_path / "application.yaml"
    config_file.write_text(yaml.safe_dump({"db": {"url": db_url}}))
    monkeypatch.setenv("ANTAREST_CONF", str(config_file))
    config = Config(str(get_local_path() / "alembic.ini"))
    config.set_main_option("script_location", str(get_local_path() / "alembic"))

    command.upgrade(config, "e12d85a77641")
    engine = create_engine(db_url)
    try:
        previous_tables = set(inspect(engine).get_table_names())
        command.upgrade(config, "3302075bbdfd")
        inspector = inspect(engine)
        assert set(inspector.get_table_names()) == previous_tables | {"gems_catalogs"}
        assert inspector.get_pk_constraint("gems_catalogs")["constrained_columns"] == ["study_data_id", "id"]
        assert {column["name"] for column in inspector.get_columns("gems_catalogs")} == {
            "study_data_id",
            "id",
            "taxonomy",
            "location",
            "metrics_definition",
        }
        foreign_key = inspector.get_foreign_keys("gems_catalogs")[0]
        assert foreign_key["constrained_columns"] == ["study_data_id"]
        assert foreign_key["referred_table"] == "study_data"
        assert foreign_key["referred_columns"] == ["study_data_id"]
        assert foreign_key["options"]["ondelete"] == "CASCADE"

        command.downgrade(config, "e12d85a77641")
        assert set(inspect(engine).get_table_names()) == previous_tables
        command.upgrade(config, "3302075bbdfd")
        assert set(inspect(engine).get_table_names()) == previous_tables | {"gems_catalogs"}
    finally:
        engine.dispose()
