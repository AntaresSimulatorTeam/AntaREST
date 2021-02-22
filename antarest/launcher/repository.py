from typing import Optional, List

from sqlalchemy.orm import Session

from antarest.launcher.model import JobResult


class JobResultRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, job: JobResult) -> JobResult:
        self.session.add(job)
        self.session.commit()
        return job

    def get(self, id: int) -> Optional[JobResult]:
        job: JobResult = self.session.query(JobResult).get(id)
        return job

    def get_all(self) -> List[JobResult]:
        jobs: List[JobResult] = self.session.query(JobResult).all()
        return jobs

    def delete(self, id: int) -> None:
        g = self.session.query(JobResult).get(id)
        self.session.delete(g)
        self.session.commit()
