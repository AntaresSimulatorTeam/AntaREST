from typing import Optional, List

from sqlalchemy import exists  # type: ignore

from antarest.core.jwt import JWTUser
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.launcher.model import JobResult
from antarest.study.service import StudyService
from antarest.study.storage.permissions import (
    check_permission,
    StudyPermissionType,
)


class JobResultRepository:
    def __init__(self, study_service: StudyService) -> None:
        self.study_service = study_service

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

    def _filter_from_user_permission(
        self, jobs_results: List[JobResult], user: Optional[JWTUser]
    ) -> List[JobResult]:
        if not user:
            return []

        allowed_job_results = []
        for job_result in jobs_results:
            if check_permission(
                user,
                self.study_service.get_study(job_result.study_id),
                StudyPermissionType.RUN,
            ):
                allowed_job_results.append(job_result)
        return allowed_job_results

    def get_all(self, user: Optional[JWTUser]) -> List[JobResult]:
        job_results: List[JobResult] = db.session.query(JobResult).all()
        return self._filter_from_user_permission(job_results, user)

    def find_by_study(
        self, study_id: str, user: Optional[JWTUser]
    ) -> List[JobResult]:
        job_results: List[JobResult] = (
            db.session.query(JobResult)
            .filter(JobResult.study_id == study_id)
            .all()
        )
        return self._filter_from_user_permission(job_results, user)

    def delete(self, id: str) -> None:
        g = db.session.query(JobResult).get(id)
        db.session.delete(g)
        db.session.commit()
