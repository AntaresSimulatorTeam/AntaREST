from typing import Optional, List

from sqlalchemy import exists  # type: ignore

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.launcher.model import JobResult


class JobResultRepository:
    def __init__(self) -> None:
        pass

    def save(self, job: JobResult) -> JobResult:
        res = db.session.query(exists().where(JobResult.id == job.id)).scalar()
        if res:
            db.session.merge(job)
        else:
            db.session.add(job)

        db.session.commit()
        return job

    def get(self, id: str) -> Optional[JobResult]:
        job: JobResult = db.session.query(JobResult).get(id)
        return job

    def get_all(self) -> List[JobResult]:
        job_results: List[JobResult] = db.session.query(JobResult).all()
        return job_results

    def find_by_study(self, study_id: str) -> List[JobResult]:
        job_results: List[JobResult] = (
            db.session.query(JobResult)
            .filter(JobResult.study_id == study_id)
            .all()
        )
        return job_results

    def delete(self, id: str) -> None:
        g = db.session.query(JobResult).get(id)
        db.session.delete(g)
        db.session.commit()
