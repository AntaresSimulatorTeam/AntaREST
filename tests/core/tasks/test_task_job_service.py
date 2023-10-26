import datetime

from sqlalchemy.orm import Session  # type: ignore

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
