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
from pathlib import Path

from antarest.core.config import Config
from antarest.core.utils.utils import get_local_path
from antarest.launcher.adapters.slurm_launcher.slurm_launcher import WORKSPACE_LOCK_FILE_NAME

logger = logging.getLogger(__name__)


def get_config(config_path: Path) -> Config:
    res = get_local_path() / "resources"
    config_obj = Config.from_yaml_file(res=res, file=config_path)
    return config_obj


def clean_locks_from_config(config: Config) -> None:
    for slurm_config in config.launcher.get_slurm_configs():
        slurm_workspace = slurm_config.local_workspace
        if slurm_workspace.exists() and slurm_workspace.is_dir():
            for workspace in slurm_workspace.iterdir():
                lock_file = workspace / WORKSPACE_LOCK_FILE_NAME
                if lock_file.exists():
                    logger.info(f"Removing slurm workspace lock file {lock_file}")
                    lock_file.unlink()


def clean_locks(config: Path) -> None:
    """Clean app locks"""
    config_obj = get_config(config)
    clean_locks_from_config(config_obj)


# TODO CHECK IF OK
def reindex_table(config: Path) -> None:
    import sqlalchemy
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    from psycopg2.extensions import connection as Psycopg2Connection

    config_obj = get_config(config)
    assert config_obj.db.db_admin_url is not None, "db_admin_url ne peut pas être None"

    engine = sqlalchemy.create_engine(str(config_obj.db.db_admin_url), echo=False)

    raw_conn = engine.raw_connection()
    try:
        conn: Psycopg2Connection = raw_conn.connection  # type: ignore[attr-defined]
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

        with conn.cursor() as cursor:
            cursor.execute("VACUUM ANALYSE study")
            cursor.execute("REINDEX INDEX study_pkey")
            cursor.execute("VACUUM ANALYSE rawstudy")
            cursor.execute("REINDEX INDEX rawstudy_pkey")
    finally:
        raw_conn.close()
