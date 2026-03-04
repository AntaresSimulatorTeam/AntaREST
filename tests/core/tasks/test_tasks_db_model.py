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
import datetime
import uuid

import pytest
from helpers import create_raw_study
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from antarest.core.tasks.model import TaskJob, TaskJobLog
from antarest.core.utils.utils import current_time
from antarest.login.model import Password, User
from antarest.study.model import RawStudy


def test_database_constraints(db_session: Session) -> None:
    # Data insertion example
    with db_session:
        task_job = TaskJob(id=str(uuid.uuid4()), name="TaskJob 1")
        log1 = TaskJobLog(job=task_job, message="'message 1'")
        log2 = TaskJobLog(job=task_job, message="'message 2'")
        db_session.add_all([task_job, log1, log2])
        db_session.commit()

    # Check that a TaskJobLog cannot be inserted without a TaskJob
    with db_session:
        with pytest.raises(IntegrityError, match="NOT NULL constraint failed"):
            db_session.add(TaskJobLog(message="'message 3'"))
            db_session.commit()

    # Delete a TaskJob object (the corresponding TaskJobLog will be deleted in cascade)
    with db_session:
        db_session.delete(task_job)
        db_session.commit()

    # Check that a TaskJob and its TaskJobLog are deleted in cascade
    with db_session:
        assert db_session.query(TaskJob).count() == 0
        assert db_session.query(TaskJobLog).count() == 0


def test_owner_constraints(db_session: Session) -> None:
    # Insert a user and attach several TaskJob objects to him
    with db_session:
        db_session.add(User(id=0o007, name="James Bond", password=Password("007")))
        db_session.commit()

    with db_session:
        task_job_1 = TaskJob(id=str(uuid.uuid4()), name="TaskJob 1", owner_id=0o007)
        task_job_2 = TaskJob(id=str(uuid.uuid4()), name="TaskJob 2", owner_id=0o007)
        task_job_3 = TaskJob(id=str(uuid.uuid4()), name="TaskJob 3", owner_id=0o007)
        db_session.add_all([task_job_1, task_job_2, task_job_3])
        db_session.commit()

    # Delete a User object (the corresponding TaskJob will not be deleted in cascade)
    # Instead, the owner_id will be set to NULL
    with db_session:
        user = db_session.query(User).first()
        db_session.delete(user)
        db_session.commit()

    # Check that the owner_id of the TaskJob objects has been set to NULL
    with db_session:
        assert db_session.query(TaskJob).filter(TaskJob.owner_id == 0o007).count() == 0
        # noinspection PyUnresolvedReferences
        assert db_session.query(TaskJob).filter(TaskJob.owner_id.is_(None)).count() == 3


def test_study_constraints(db_session: Session) -> None:
    # Insert a Study object and attach several TaskJob objects to it
    with db_session:
        study_id = str(uuid.uuid4())
        db_session.add(create_raw_study(id=study_id, name="Study 1", version="8.8"))
        db_session.commit()

    with db_session:
        task_job_1 = TaskJob(id=str(uuid.uuid4()), name="TaskJob 1", ref_id=study_id)
        task_job_2 = TaskJob(id=str(uuid.uuid4()), name="TaskJob 2", ref_id=study_id)
        task_job_3 = TaskJob(id=str(uuid.uuid4()), name="TaskJob 3", ref_id=study_id)
        db_session.add_all([task_job_1, task_job_2, task_job_3])
        db_session.commit()

    # Delete a Study object (the corresponding TaskJob must be deleted in cascade)
    with db_session:
        study = db_session.query(RawStudy).first()
        db_session.delete(study)
        db_session.commit()

    # Check that the owner_id of the TaskJob objects has been set to NULL
    with db_session:
        assert db_session.query(TaskJob).count() == 0


def test_database_date_utc(db_session: Session) -> None:
    now = current_time()
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
        task_job.completion_date = current_time()
        db_session.commit()

    with db_session:
        task_job = db_session.query(TaskJob).filter(TaskJob.name == "foo").one()
        assert task_job.completion_date is not None
        assert now <= task_job.creation_date <= task_job.completion_date <= later
