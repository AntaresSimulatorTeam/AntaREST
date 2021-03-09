from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from antarest.common.persistence import Base
from antarest.launcher.model import JobResult, JobStatus
from antarest.launcher.repository import JobResultRepository


@pytest.mark.unit_test
def test_job_result() -> None:
    engine = create_engine("sqlite:///:memory:", echo=True)
    session = scoped_session(
        sessionmaker(autocommit=False, autoflush=False, bind=engine)
    )
    Base.metadata.create_all(engine)

    repo = JobResultRepository(session=session)
    study_id = str(uuid4())
    a = JobResult(
        id=str(uuid4()),
        study_id=study_id,
        job_status=JobStatus.SUCCESS,
        msg="Hello, World!",
        exit_code=0,
    )
    b = JobResult(
        id=str(uuid4()),
        job_status=JobStatus.FAILED,
        msg="You failed !!",
        exit_code=1,
    )

    a = repo.save(a)
    b = repo.save(b)
    c = repo.get(a.id)
    assert a == c

    d = repo.find_by_study(study_id)
    assert len(d) == 1
    assert a == d[0]

    repo.delete(a.id)
    assert repo.get(a.id) is None

    assert len(repo.find_by_study(study_id)) == 0


@pytest.mark.unit_test
def test_update_object():
    engine = create_engine("sqlite:///:memory:", echo=True)
    session = scoped_session(
        sessionmaker(autocommit=False, autoflush=False, bind=engine)
    )
    Base.metadata.create_all(engine)

    repo = JobResultRepository(session=session)
    uuid = str(uuid4())
    a = JobResult(
        id=uuid,
        job_status=JobStatus.SUCCESS,
        msg="Hello, World!",
        exit_code=0,
    )
    b = JobResult(
        id=uuid,
        job_status=JobStatus.FAILED,
        msg="You failed !!",
        exit_code=1,
    )

    c = repo.save(a)
    d = repo.save(b)
    assert c != d
