from typing import Optional, List

from sqlalchemy import exists  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from antarest.launcher.model import JobResult


class JobResultRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, job: JobResult) -> JobResult:
        res = self.session.query(
            exists().where(JobResult.id == job.id)
        ).scalar()
        if res:
            self.session.merge(job)
        else:
            self.session.add(job)

        self.session.commit()
        return job

    def get(self, id: str) -> Optional[JobResult]:
        job: JobResult = self.session.query(JobResult).get(id)
        return job

    def get_all(self) -> List[JobResult]:
        jobs: List[JobResult] = self.session.query(JobResult).all()
        return jobs

    def delete(self, id: str) -> None:
        g = self.session.query(JobResult).get(id)
        self.session.delete(g)
        self.session.commit()
