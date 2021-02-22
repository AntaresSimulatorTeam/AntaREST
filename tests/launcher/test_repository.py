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
    a = JobResult(
        id=str(uuid4()),
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

    repo.delete(a.id)
    assert repo.get(a.id) is None
