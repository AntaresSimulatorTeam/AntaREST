import datetime
import logging
from typing import Optional, List

from sqlalchemy import exists  # type: ignore

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.launcher.model import JobResult, JobLogType, JobLog
from antarest.study.model import Study

logger = logging.getLogger(__name__)


class JobResultRepository:
    def __init__(self) -> None:
        pass

    def save(self, job: JobResult) -> JobResult:
        logger.debug(f"Saving JobResult {job.id}")
        res = db.session.query(exists().where(JobResult.id == job.id)).scalar()
        if res:
            db.session.merge(job)
        else:
            db.session.add(job)

        db.session.commit()
        return job

    def get(self, id: str) -> Optional[JobResult]:
        logger.debug(f"Retrieving JobResult {id}")
        job: JobResult = db.session.query(JobResult).get(id)
        return job

    def get_all(
        self, filter_orphan: bool = False, latest: Optional[int] = None
    ) -> List[JobResult]:
        logger.debug("Retrieving all JobResults")
        query = db.session.query(JobResult)
        if filter_orphan:
            query = query.join(Study, JobResult.study_id == Study.id)
        query = query.order_by(JobResult.creation_date.desc())
        if latest:
            query = query.limit(latest)
        job_results: List[JobResult] = query.all()
        return job_results

    def get_running(self) -> List[JobResult]:
        query = db.session.query(JobResult).where(
            JobResult.completion_date == None
        )
        job_results: List[JobResult] = query.all()
        return job_results

    def find_by_study(self, study_id: str) -> List[JobResult]:
        logger.debug(f"Retrieving JobResults from study {study_id}")
        job_results: List[JobResult] = (
            db.session.query(JobResult)
            .filter(JobResult.study_id == study_id)
            .all()
        )
        return job_results

    def delete(self, id: str) -> None:
        logger.debug(f"Deleting JobResult {id}")
        g = db.session.query(JobResult).get(id)
        db.session.delete(g)
        db.session.commit()

    def delete_by_study_id(self, study_id: str) -> None:
        logger.debug(f"Deleting JobResults from_study {study_id}")
        jobs = (
            db.session.query(JobResult)
            .filter(JobResult.study_id == study_id)
            .all()
        )
        for job in jobs:
            db.session.delete(job)
        db.session.commit()
