import logging
from typing import Optional, List

from sqlalchemy import exists  # type: ignore

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.launcher.model import JobResult

logger = logging.getLogger(__name__)


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
        logger.debug(f"JobResult {job.id} saved")
        return job

    def get(self, id: str) -> Optional[JobResult]:
        logger.debug(f"Retrieving JobResult {id}")
        job: JobResult = db.session.query(JobResult).get(id)
        return job

    def get_all(self) -> List[JobResult]:
        job_results: List[JobResult] = db.session.query(JobResult).all()
        logger.debug(f"All JobResults retrieved")
        return job_results

    def find_by_study(self, study_id: str) -> List[JobResult]:
        job_results: List[JobResult] = (
            db.session.query(JobResult)
            .filter(JobResult.study_id == study_id)
            .all()
        )
        logger.debug(f"JobResults with study_id {study_id} retrieved")
        return job_results

    def delete(self, id: str) -> None:
        g = db.session.query(JobResult).get(id)
        db.session.delete(g)
        db.session.commit()
        logger.debug(f"JobResult {id} deleted")

    def delete_by_study_id(self, study_id: str) -> None:
        db.session.query(JobResult).filter(
            JobResult.study_id == study_id
        ).delete()
        db.session.commit()
        logger.debug(f"JobResults with study_id {study_id} deleted")
