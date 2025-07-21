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

import datetime

from sqlalchemy.orm import Session

from antarest.core.tasks.model import TaskJob


def test_database_date_utc(db_session: Session) -> None:
    now = datetime.datetime.utcnow()
    later = now + datetime.timedelta(seconds=1)

    with db_session:
        task_job = TaskJob(name="foo")
        db_session.add(task_job)
        db_session.commit()

    with db_session:
        task_job = db_session.query(TaskJob).filter(TaskJob.name == "foo").one()
        assert now <= task_job.creation_date <= later
        assert task_job.completion_date is None

    with db_session:
        task_job = db_session.query(TaskJob).filter(TaskJob.name == "foo").one()
        task_job.completion_date = datetime.datetime.utcnow()
        db_session.commit()

    with db_session:
        task_job = db_session.query(TaskJob).filter(TaskJob.name == "foo").one()
        assert now <= task_job.creation_date <= task_job.completion_date <= later
