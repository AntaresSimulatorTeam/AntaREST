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
"""Exercise the new migration with existing data and enforced foreign keys."""

import importlib.util
import json
import os
import uuid
from pathlib import Path

import pytest
import sqlalchemy as sa
import yaml
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy.orm import Session

from alembic import command
from antarest.output.storage.v2.dbmodel import DbOutputMetadataV2, DbParquetArea, DbParquetVariable
from antarest.output.storage.v2.metadata import ParquetOutputMetadata

ROOT = Path(__file__).parents[2]
PREVIOUS = "0974bca4078d"
MIGRATION = ROOT / "alembic/versions/afdea905eb28_normalize_parquet_output_metadata.py"


@pytest.fixture(params=["sqlite", "postgresql"])
def migration_db(request, tmp_path, monkeypatch):
    admin = None
    if request.param == "sqlite":
        url = f"sqlite:///{tmp_path / 'migration.sqlite'}"
    else:
        address = os.environ.get("PARQUET_TEST_POSTGRES_URL")
        if not address:
            pytest.skip("Set PARQUET_TEST_POSTGRES_URL to test on an isolated PostgreSQL database")
        admin = sa.create_engine(address, isolation_level="AUTOCOMMIT")
        database = "parquet_test_" + uuid.uuid4().hex
        with admin.connect() as conn:
            conn.execute(sa.text(f'CREATE DATABASE "{database}"'))
        url = str(sa.engine.make_url(address).set(database=database).render_as_string(hide_password=False))
    config_file = tmp_path / "config.yml"
    config_file.write_text(yaml.safe_dump({"db": {"url": url}}))
    monkeypatch.setenv("ANTAREST_CONF", str(config_file))
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "alembic"))
    command.upgrade(cfg, PREVIOUS)
    engine = sa.create_engine(url)
    if request.param == "sqlite":
        sa.event.listen(engine, "connect", lambda connection, _: connection.execute("PRAGMA foreign_keys=ON"))
    spec = importlib.util.spec_from_file_location("parquet_metadata_migration", MIGRATION)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        yield engine, module
    finally:
        engine.dispose()
        if admin is not None:
            with admin.connect() as conn:
                conn.execute(sa.text(f'DROP DATABASE "{database}"'))
            admin.dispose()


def _seed(engine):
    values = {
        "mc_ind": {
            "areas": [
                {
                    "name": "fr",
                    "variables": ["LOAD", "FR_ONLY"],
                    "thermal_clusters": [{"name": "nuclear", "variables": ["MWh", "NP Cost - Euro"]}],
                    "renewable_clusters": [],
                    "short_term_storages": [],
                }
            ],
            "links": [{"area_1_name": "fr", "area_2_name": "es", "variables": ["FLOW"]}],
        },
        "mc_all": {"areas": [], "links": []},
    }
    meta = sa.MetaData()
    output = sa.Table("output_v2_metadata", meta, autoload_with=engine)
    logs = sa.Table("output_v2_logs", meta, autoload_with=engine)
    blob = sa.Table("output_v2_variables", meta, autoload_with=engine)
    with engine.begin() as conn:
        for name in ("first", "second"):
            conn.execute(
                output.insert().values(
                    study_id="study",
                    output_name=name,
                    archived=name == "second",
                    mode="Economy",
                    synthesis=True,
                    by_year=True,
                    nb_years=2,
                    start_month=1,
                    january_first_weekday=1,
                    leap_year=False,
                    start_day=1,
                    end_day=365,
                    first_weekday=1,
                )
            )
            conn.execute(logs.insert().values(study_id="study", output_id=name, out="preserved", err=""))
            conn.execute(
                blob.insert().values(
                    study_id="study", output_id=name, variables_list_version=1, variables_list=json.dumps(values)
                )
            )
    return values


def _run(engine, module, operation):
    with engine.begin() as conn:
        with Operations.context(MigrationContext.configure(conn)):
            getattr(module, operation)()


def test_upgrade_preserves_outputs_logs_and_variable_lists(migration_db):
    engine, module = migration_db
    expected = _seed(engine)
    _run(engine, module, "upgrade")
    with Session(engine) as session:
        rows = session.scalars(sa.select(DbOutputMetadataV2).order_by(DbOutputMetadataV2.output_name)).all()
        assert len(rows) == 2
        assert rows[0].id != rows[1].id
        assert rows[0].metadata_version == rows[1].metadata_version == 0
        assert not rows[0].archived and rows[1].archived
        assert rows[0].mc_years == []
        actual = ParquetOutputMetadata(session, rows[0].id).get_variables_list().model_dump()
        expected["mc_ind"]["areas"][0]["variables"].sort()
        assert actual == expected
        assert session.execute(sa.text("SELECT count(*) FROM output_v2_logs WHERE out='preserved'")).scalar() == 2
        assert "output_v2_variables" not in sa.inspect(engine).get_table_names()
        # New imports allocate a fresh integer key after migration on both databases.
        new = DbOutputMetadataV2(
            study_id="study",
            output_name="new",
            archived=False,
            mode="Economy",
            synthesis=False,
            by_year=False,
            nb_years=0,
            start_month=1,
            january_first_weekday=1,
            leap_year=False,
            start_day=1,
            end_day=365,
            first_weekday=1,
        )
        session.add(new)
        session.flush()
        assert new.id not in {r.id for r in rows}
        session.delete(rows[0])
        session.flush()
        assert (
            session.scalar(
                sa.select(sa.func.count()).select_from(DbParquetArea).where(DbParquetArea.output_id == rows[0].id)
            )
            == 0
        )
        assert (
            session.scalar(
                sa.select(sa.func.count())
                .select_from(DbParquetVariable)
                .where(DbParquetVariable.output_id == rows[0].id)
            )
            == 0
        )
        assert session.execute(sa.text("SELECT count(*) FROM output_v2_logs")).scalar() == 1


def test_downgrade_preserves_legacy_data_and_can_upgrade_again(migration_db):
    engine, module = migration_db
    expected = _seed(engine)
    _run(engine, module, "upgrade")
    _run(engine, module, "downgrade")
    with engine.connect() as conn:
        blobs = conn.execute(sa.text("SELECT variables_list FROM output_v2_variables")).scalars().all()
        assert len(blobs) == 2
        expected["mc_ind"]["areas"][0]["variables"].sort()
        assert all(json.loads(blob) == expected for blob in blobs)
        assert conn.execute(sa.text("SELECT count(*) FROM output_v2_logs WHERE out='preserved'")).scalar() == 2
    _run(engine, module, "upgrade")
    assert "output_v2_variables" not in sa.inspect(engine).get_table_names()
