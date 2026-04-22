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

import logging
import time
from pathlib import Path

from sqlalchemy import Engine, create_engine, update

from antarest.core.config import Config
from antarest.core.tasks.model import TaskJob, TaskStatus
from antarest.core.utils.utils import current_time, get_local_path

logger = logging.getLogger(__name__)


def _create_engine(config: Config) -> Engine:
    url = config.db.db_admin_url
    assert url is not None, "db_admin_url can not be None"
    return create_engine(url, echo=False)


def _create_config(config_path: Path) -> Config:
    res = get_local_path() / "resources"
    config_obj = Config.from_yaml_file(res=res, file=config_path)
    return config_obj


def reindex_table(config: Path) -> None:
    import sqlalchemy
    from sqlalchemy import text

    config_obj = _create_config(config)
    assert config_obj.db.db_admin_url is not None, "db_admin_url can not be None"

    engine = sqlalchemy.create_engine(str(config_obj.db.db_admin_url), echo=False)

    with engine.connect() as connection, connection.begin():
        connection = connection.execution_options(autocommit=True)
        connection.execute(text("VACUUM ANALYSE study"))
        connection.execute(text("REINDEX INDEX study_pkey"))
        connection.execute(text("VACUUM ANALYSE rawstudy"))
        connection.execute(text("REINDEX INDEX rawstudy_pkey"))


def _do_fix_interrupted_tasks_status(engine: Engine) -> None:
    updated_values = {
        TaskJob.status: TaskStatus.FAILED.value,
        TaskJob.result_status: False,
        TaskJob.result_msg: "Task was interrupted due to server restart",
        TaskJob.completion_date: current_time(),
    }
    orphan_status = [TaskStatus.RUNNING.value, TaskStatus.PENDING.value]
    logger.info("Setting status of interrupted tasks to FAILED.")
    t0 = time.time()
    with engine.connect() as connection:
        stmt = update(TaskJob).where(TaskJob.status.in_(orphan_status)).values(updated_values)
        connection.execute(stmt)
        connection.commit()
    logger.info(f"Tasks status correctly updated in {time.time() - t0}s.")


def fix_interrupted_tasks_status(config_file: Path) -> None:
    """
    Cancel all tasks that are currently running or pending.

    When the web application restarts, such as after a new deployment, any pending or running tasks may be lost.
    To mitigate this, it is preferable to set these tasks to a "FAILED" status.
    This ensures that users can easily identify the tasks that were affected by the restart and take appropriate
    actions, such as restarting the tasks manually.
    """
    config = _create_config(config_file)
    engine = _create_engine(config)
    _do_fix_interrupted_tasks_status(engine)
