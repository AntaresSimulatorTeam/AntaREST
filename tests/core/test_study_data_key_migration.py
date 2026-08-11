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
Data-bearing tests of the `1f0c9b2e7a34` migration, which replaces the `study_id` carried by
every study data table with the `study_data.study_data_id` surrogate key.

`tests/core/test_alembic_migration.py` runs the migrations on an empty database: it proves they
execute, not that they carry the data over. These tests seed two studies at the previous revision
and check, after the upgrade, that every row is still there and still attached to the study it
was seeded for.
"""

import os
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any, Dict, Iterator, List

import pytest
import sqlalchemy as sa
import yaml
from alembic.config import Config
from sqlalchemy.engine import Engine

from alembic import command
from antarest.core.utils.utils import get_local_path
from antarest.dbmodel import Base
from antarest.study.business.model.user_model import ResourceType
from antarest.study.dao.database.models.area import AREA_TABLE, AREA_UI_TABLE, LOAD_TABLE  # noqa: F401
from antarest.study.dao.database.models.layer import LAYER_TABLE  # noqa: F401
from antarest.study.dao.database.models.thermal import THERMAL_CLUSTER_TABLE, THERMAL_SERIES_TABLE  # noqa: F401
from antarest.study.dao.database.models.user_resources import USER_RESOURCES_TABLE  # noqa: F401
from antarest.study.model import Study  # noqa: F401
from tests.integration.conftest import RUN_ON_WINDOWS

REVISION = "1f0c9b2e7a34"
PREVIOUS_REVISION = "6012b0407e38"

REFERENCE_TABLE = "study_data"
STRING_KEY = "study_id"
SURROGATE_KEY = "study_data_id"

# One representative table per shape the migration has to handle: a direct child of `study_data`,
# a child reached through a two-column composite key, one reached through a three-column one, a
# matrix table (what the matrix garbage collector walks), and the only table whose study key is
# not part of its primary key. Parents come before children: they are inserted in this order.
SEEDED_TABLES = ["layer", "area", "area_ui", "load", "thermal_cluster", "thermal_series", "user_resources"]


def _seeded_rows(tag: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    The identifying columns of the rows seeded for one study. Every other column is filled in by
    `_row`, so that adding a column to a model does not break this test.
    """
    return {
        "layer": [{"layer_id": "0"}, {"layer_id": "1"}],
        "area": [{"area_id": "fr"}, {"area_id": "de"}],
        "area_ui": [{"area_id": "fr", "layer_id": "0"}, {"area_id": "de", "layer_id": "1"}],
        "load": [{"area_id": "fr", "matrix_id": f"load_matrix_{tag}"}],
        "thermal_cluster": [{"area_id": "fr", "thermal_id": "gas"}],
        "thermal_series": [{"area_id": "fr", "thermal_id": "gas", "matrix_id": f"series_matrix_{tag}"}],
        "user_resources": [
            {
                "id": f"resource_{tag}",
                "name": "file.txt",
                "resource_type": ResourceType.FILE.value,
                "blob_id": f"blob_{tag}",
            },
            {
                "id": f"folder_{tag}",
                "name": "my_folder",
                "resource_type": ResourceType.FOLDER.value,
                "blob_id": None,
            },
        ],
    }


#
# Alembic driving
#


def _alembic_config(tmp_path: Path, db_url: str) -> Config:
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.safe_dump({"db": {"url": db_url}}, f)
    os.environ["ANTAREST_CONF"] = str(config_file)

    alembic_cfg = Config(str(get_local_path() / "alembic.ini"))
    alembic_cfg.stdout = StringIO()
    alembic_cfg.set_main_option("script_location", str(get_local_path() / "alembic"))
    return alembic_cfg


#
# Seeding
#


def _placeholder(column: "sa.Column[Any]", tag: str) -> Any:
    """
    A value of the right type for a column the test does not care about, distinct between studies
    so that a row leaking from one study to the other cannot go unnoticed.
    """
    column_type = column.type
    # `Enum` derives from `String`, so it has to be matched first.
    if isinstance(column_type, sa.Enum):
        return column_type.enums[0]
    if isinstance(column_type, sa.Boolean):
        return False
    if isinstance(column_type, sa.String):
        value = f"{column.name}_{tag}"
        return value[: column_type.length] if column_type.length else value
    if isinstance(column_type, sa.Float):
        return 1.5
    if isinstance(column_type, sa.Integer):
        return 1
    if isinstance(column_type, sa.DateTime):
        return datetime(2026, 1, 1)
    raise NotImplementedError(f"No placeholder for {column.name} of type {column_type}")


def _row(table_name: str, tag: str, **values: Any) -> Dict[str, Any]:
    """
    Complete `values` into a full row of `table_name`, reading the column definitions from the
    models rather than from the database: at the previous revision the study key columns are
    reflected as plain strings, which loses the enum values the check constraints require.

    Every column is given a value, nullable ones included, so that the row read back after the
    migration can be compared to this one field by field.
    """
    row = dict(values)
    for column in Base.metadata.tables[table_name].columns:
        if column.name in row or column.name == SURROGATE_KEY or column.autoincrement is True:
            continue
        row[column.name] = None if column.nullable else _placeholder(column, tag)
    return row


def _seed_study(engine: Engine, study_id: str, tag: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Insert a study and its data rows at the previous revision. Returns the seeded rows, keyed by
    table, as they are expected to be found after the upgrade.
    """
    metadata = sa.MetaData()
    metadata.reflect(bind=engine, only=["study", REFERENCE_TABLE, *SEEDED_TABLES])

    seeded = {
        table: [_row(table, tag, study_id=study_id, **row) for row in rows] for table, rows in _seeded_rows(tag).items()
    }

    with engine.begin() as connection:
        connection.execute(metadata.tables["study"].insert().values(_row("study", tag, id=study_id)))
        connection.execute(metadata.tables[REFERENCE_TABLE].insert().values({STRING_KEY: study_id}))
        for table in SEEDED_TABLES:
            connection.execute(metadata.tables[table].insert(), seeded[table])
    return seeded


def _study_data_id(engine: Engine, study_id: str) -> int:
    with engine.connect() as connection:
        stmt = sa.text(f"SELECT {SURROGATE_KEY} FROM {REFERENCE_TABLE} WHERE {STRING_KEY} = :study_id")
        study_data_id: int = connection.execute(stmt, {"study_id": study_id}).scalar_one()
    return study_data_id


def _fetch(engine: Engine, table_name: str, study_data_id: int) -> List[Dict[str, Any]]:
    """
    The rows of `table_name` belonging to a study, keyed by the surrogate key instead of the
    study id, so that they can be compared to what was seeded.
    """
    metadata = sa.MetaData()
    table = sa.Table(table_name, metadata, autoload_with=engine)
    with engine.connect() as connection:
        rows = connection.execute(sa.select(table).where(table.c[SURROGATE_KEY] == study_data_id)).fetchall()
    return [{key: value for key, value in row._mapping.items() if key != SURROGATE_KEY} for row in rows]


def _sorted(rows: List[Dict[str, Any]]) -> List[List[Any]]:
    return sorted([sorted((key, str(value)) for key, value in row.items()) for row in rows])


def _assert_rows_migrated(engine: Engine, study_id: str, seeded: Dict[str, List[Dict[str, Any]]]) -> None:
    study_data_id = _study_data_id(engine, study_id)
    for table in SEEDED_TABLES:
        expected = [{key: value for key, value in row.items() if key != STRING_KEY} for row in seeded[table]]
        assert _sorted(_fetch(engine, table, study_data_id)) == _sorted(expected), (
            f"Table {table} was not migrated as expected for study {study_id}"
        )


#
# Fixtures
#


@pytest.fixture(scope="module")
def postgresql_url() -> Iterator[str]:
    if RUN_ON_WINDOWS:
        pytest.skip("Docker fails on Windows")
    from testcontainers.postgres import PostgresContainer

    with PostgresContainer("postgres:14") as postgres:
        yield postgres.get_connection_url()


@pytest.fixture(params=["sqlite", "postgresql"])
def engine(request: Any, tmp_path: Path) -> Iterator[Engine]:
    """
    An empty database, migrated up to the revision preceding the one under test.

    The PostgreSQL container is shared by the whole module — starting one per test is slow — so
    its schema is dropped between tests.
    """
    if request.param == "sqlite":
        db_url = f"sqlite:///{tmp_path / 'db.sqlite'}"
    else:
        db_url = request.getfixturevalue("postgresql_url")
        with sa.create_engine(db_url).begin() as connection:
            connection.execute(sa.text("DROP SCHEMA public CASCADE"))
            connection.execute(sa.text("CREATE SCHEMA public"))

    engine = sa.create_engine(db_url)
    if request.param == "sqlite":
        # SQLite ignores foreign keys unless they are explicitly turned on, and the test relies
        # on the cascade from `study_data`.
        sa.event.listen(
            engine, "connect", lambda dbapi_connection, _: dbapi_connection.execute("PRAGMA foreign_keys=ON")
        )

    command.upgrade(_alembic_config(tmp_path, db_url), PREVIOUS_REVISION)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def alembic_cfg(engine: Engine, tmp_path: Path) -> Config:
    return _alembic_config(tmp_path, str(engine.url.render_as_string(hide_password=False)))


#
# Tests
#


def test_upgrade_carries_study_data_over(engine: Engine, alembic_cfg: Config) -> None:
    """
    Two studies are seeded so that a backfill joining on the wrong row shows up as data of one
    study landing on the other.
    """
    first_seeded = _seed_study(engine, "study-one", "one")
    second_seeded = _seed_study(engine, "study-two", "two")

    command.upgrade(alembic_cfg, REVISION)

    _assert_rows_migrated(engine, "study-one", first_seeded)
    _assert_rows_migrated(engine, "study-two", second_seeded)
    assert _study_data_id(engine, "study-one") != _study_data_id(engine, "study-two")


def test_upgrade_replaces_the_study_key(engine: Engine, alembic_cfg: Config) -> None:
    _seed_study(engine, "study-one", "one")

    command.upgrade(alembic_cfg, REVISION)

    inspector = sa.inspect(engine)
    for table in SEEDED_TABLES:
        columns = {column["name"] for column in inspector.get_columns(table)}
        assert STRING_KEY not in columns, f"Table {table} still carries {STRING_KEY}"
        assert SURROGATE_KEY in columns

        model_columns = {column.name for column in Base.metadata.tables[table].columns}
        assert columns == model_columns, f"Table {table} does not match its model"

        primary_key = inspector.get_pk_constraint(table)["constrained_columns"]
        model_primary_key = [column.name for column in Base.metadata.tables[table].primary_key]
        assert primary_key == model_primary_key, f"Primary key of {table} does not match its model"

    # `user_resources` is the one table whose study key is not covered by its primary key: it is
    # the only one to need an explicit index, the others would only duplicate their primary key.
    for table in SEEDED_TABLES:
        indexed = any(index["column_names"] == [SURROGATE_KEY] for index in inspector.get_indexes(table))
        if table == "user_resources":
            assert indexed, "The foreign key of user_resources is left unindexed"
        else:
            assert not indexed, f"Table {table} carries an index duplicating its primary key"

    reference_columns = {column["name"] for column in inspector.get_columns(REFERENCE_TABLE)}
    assert reference_columns == {STRING_KEY, SURROGATE_KEY}
    assert inspector.get_pk_constraint(REFERENCE_TABLE)["constrained_columns"] == [SURROGATE_KEY]


def test_upgrade_preserves_the_cascade_from_study(engine: Engine, alembic_cfg: Config) -> None:
    """
    Clearing a study's data is a single `DELETE` on `study_data`, which is the reason that table
    exists. Re-pointing every foreign key must not break it.
    """
    _seed_study(engine, "study-one", "one")
    second_seeded = _seed_study(engine, "study-two", "two")

    command.upgrade(alembic_cfg, REVISION)
    first_id = _study_data_id(engine, "study-one")

    with engine.begin() as connection:
        connection.execute(sa.text(f"DELETE FROM {REFERENCE_TABLE} WHERE {STRING_KEY} = 'study-one'"))

    with engine.connect() as connection:
        for table in SEEDED_TABLES:
            remaining = connection.execute(sa.text(f'SELECT COUNT(*) FROM "{table}"')).scalar_one()
            assert remaining == len(second_seeded[table]), f"Deleting a study did not clear {table}"
            assert _fetch(engine, table, first_id) == []
    _assert_rows_migrated(engine, "study-two", second_seeded)


def test_downgrade_restores_the_schema(engine: Engine, alembic_cfg: Config) -> None:
    """
    The downgrade is schema-only by design: it rebuilds the data tables empty. What it must
    restore exactly is the schema, so that a subsequent upgrade finds what it expects.
    """
    _seed_study(engine, "study-one", "one")
    before = _schema(engine)
    # Guards against comparing two snapshots that describe nothing.
    assert before[REFERENCE_TABLE]["primary_key"] == [STRING_KEY]
    assert STRING_KEY in before["area"]["columns"]

    command.upgrade(alembic_cfg, REVISION)
    command.downgrade(alembic_cfg, PREVIOUS_REVISION)

    assert _schema(engine) == before

    with engine.connect() as connection:
        # Data loss is expected — but only of the study data, not of the studies themselves.
        for table in SEEDED_TABLES:
            assert connection.execute(sa.text(f'SELECT COUNT(*) FROM "{table}"')).scalar_one() == 0
        assert connection.execute(sa.text(f"SELECT {STRING_KEY} FROM {REFERENCE_TABLE}")).scalars().all() == [
            "study-one"
        ]
        assert connection.execute(sa.text("SELECT id FROM study")).scalars().all() == ["study-one"]

    # The rebuilt schema is the one the upgrade was written against.
    command.upgrade(alembic_cfg, REVISION)
    assert _study_data_id(engine, "study-one") is not None


def _schema(engine: Engine) -> Dict[str, Any]:
    """
    The parts of the schema the migration rewrites, in a form that can be compared across the
    upgrade/downgrade round trip.

    Constraint and index names are dropped: PostgreSQL and SQLite name them differently, and the
    migration renames some on the way. Column order is dropped too: PostgreSQL cannot insert a
    column in the middle of a table, so the downgrade appends the restored `study_id`.
    """
    inspector = sa.inspect(engine)
    schema = {}
    for table in sorted(inspector.get_table_names()):
        schema[table] = {
            "columns": {
                column["name"]: (str(column["type"]), column["nullable"]) for column in inspector.get_columns(table)
            },
            "primary_key": inspector.get_pk_constraint(table)["constrained_columns"],
            "foreign_keys": sorted(
                (
                    tuple(fk["constrained_columns"]),
                    fk["referred_table"],
                    tuple(fk["referred_columns"]),
                    fk["options"].get("ondelete"),
                )
                for fk in inspector.get_foreign_keys(table)
            ),
            "indexes": sorted(
                (tuple(index["column_names"]), bool(index["unique"])) for index in inspector.get_indexes(table)
            ),
        }
    return schema
