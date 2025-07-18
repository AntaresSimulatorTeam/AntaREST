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
from unittest.mock import Mock
from uuid import uuid4

import pytest

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.launcher.model import JobLog, JobLogType, JobResult, JobStatus
from antarest.launcher.repository import JobResultRepository
from antarest.login.model import Identity
from antarest.study.repository import StudyMetadataRepository
from tests.helpers import create_raw_study, with_db_context


@pytest.mark.unit_test
@with_db_context
def test_job_result() -> None:
    repo = JobResultRepository()
    study_id = str(uuid4())
    study_repo = StudyMetadataRepository(Mock())
    study_repo.save(create_raw_study(id=study_id))
    a = JobResult(
        id=str(uuid4()),
        study_id=study_id,
        job_status=JobStatus.SUCCESS,
        msg="Hello, World!",
        exit_code=0,
    )
    b = JobResult(
        id=str(uuid4()),
        study_id=study_id,
        job_status=JobStatus.FAILED,
        creation_date=datetime.datetime.utcfromtimestamp(1655136710),
        completion_date=datetime.datetime.utcfromtimestamp(1655136720),
        msg="You failed !!",
        exit_code=1,
    )
    b2 = JobResult(
        id=str(uuid4()),
        study_id=study_id,
        job_status=JobStatus.FAILED,
        creation_date=datetime.datetime.utcfromtimestamp(1655136740),
        msg="You failed !!",
        exit_code=1,
    )
    b3 = JobResult(
        id=str(uuid4()),
        study_id="other_study",
        job_status=JobStatus.FAILED,
        creation_date=datetime.datetime.utcfromtimestamp(1655136729),
        msg="You failed !!",
        exit_code=1,
    )

    a = repo.save(a)
    b = repo.save(b)
    b2 = repo.save(b2)
    b3 = repo.save(b3)
    c = repo.get(a.id)
    assert a == c

    d = repo.find_by_study(study_id)
    assert len(d) == 3
    assert a == d[0]

    running = repo.get_running()
    assert len(running) == 3

    all = repo.get_all()
    assert len(all) == 4
    assert all[0] == a
    assert all[1] == b2
    assert all[2] == b3
    assert all[3] == b

    all = repo.get_all(filter_orphan=True)
    assert len(all) == 3

    all = repo.get_all(latest=2)
    assert len(all) == 2

    repo.delete(a.id)
    assert repo.get(a.id) is None

    assert len(repo.find_by_study(study_id)) == 2

    repo.delete_by_study_id(study_id=study_id)
    assert repo.get(b.id) is None
    assert repo.get(b2.id) is None
    assert repo.get(b3.id) is not None


@pytest.mark.unit_test
@with_db_context
def test_update_object():
    identity = Identity(id=1, name="test")
    db.session.add(identity)
    db.session.commit()
    owner_id = identity.id

    a = JobResult(
        id=str(uuid4()),
        study_id="a",
        job_status=JobStatus.SUCCESS,
        msg="Hello, World!",
        exit_code=0,
        owner_id=owner_id,
    )
    b = JobResult(
        id=str(uuid4()),
        study_id="b",
        job_status=JobStatus.FAILED,
        msg="You failed !!",
        exit_code=1,
        owner_id=owner_id,
    )

    repo = JobResultRepository()
    c = repo.save(a)
    d = repo.save(b)
    assert c != d


@pytest.mark.unit_test
@with_db_context
def test_logs():
    repo = JobResultRepository()
    uuid = str(uuid4())
    a = JobResult(
        id=uuid,
        study_id="a",
        job_status=JobStatus.SUCCESS,
        msg="Hello, World!",
        exit_code=0,
    )

    repo.save(a)
    a.logs.append(JobLog(job_id=uuid, message="a", log_type=JobLogType.BEFORE))
    repo.save(a)
    job_log_id = a.logs[0].id
    a.logs.append(JobLog(job_id=uuid, message="b", log_type=JobLogType.BEFORE))
    a.logs.append(JobLog(job_id=uuid, message="c", log_type=JobLogType.AFTER))
    b = repo.save(a)
    c = repo.get(uuid)
    assert b.logs == c.logs
    assert b.logs[0].id == job_log_id
    assert b.logs[0].message == "a"
    assert b.logs[0].log_type == JobLogType.BEFORE
    assert b.logs[0].job_id == uuid
