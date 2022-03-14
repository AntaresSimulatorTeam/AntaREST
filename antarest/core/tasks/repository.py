import datetime
from http import HTTPStatus
from operator import and_
from typing import Optional, List, Any

from fastapi import HTTPException

from antarest.core.tasks.model import TaskJob, TaskListFilter
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import assert_this


class TaskJobRepository:
    def save(self, task: TaskJob) -> TaskJob:
        task = db.session.merge(task)
        db.session.add(task)
        db.session.commit()
        return task

    def get(self, id: str) -> Optional[TaskJob]:
        task: TaskJob = db.session.get(TaskJob, id)
        if task is not None:
            db.session.refresh(task)
        return task

    def get_or_raise(self, id: str) -> TaskJob:
        task = self.get(id)
        if task is None:
            raise HTTPException(HTTPStatus.NOT_FOUND, f"Task {id} not found")
        return task

    @staticmethod
    def _combine_clauses(where_clauses: List[Any]) -> Any:
        assert_this(len(where_clauses) > 0)
        if len(where_clauses) > 1:
            return and_(
                where_clauses[0],
                TaskJobRepository._combine_clauses(where_clauses[1:]),
            )
        else:
            return where_clauses[0]

    def list(
        self, filter: TaskListFilter, user: Optional[int] = None
    ) -> List[TaskJob]:
        query = db.session.query(TaskJob)
        where_clauses: List[Any] = []
        if user:
            where_clauses.append(TaskJob.owner_id == user)
        if len(filter.status) > 0:
            where_clauses.append(
                TaskJob.status.in_([status.value for status in filter.status])
            )
        if filter.name:
            where_clauses.append(TaskJob.name.ilike(f"%{filter.name}%"))
        if filter.to_creation_date_utc:
            where_clauses.append(
                TaskJob.creation_date.__le__(
                    datetime.datetime.fromtimestamp(
                        filter.to_creation_date_utc
                    )
                )
            )
        if filter.from_creation_date_utc:
            where_clauses.append(
                TaskJob.creation_date.__ge__(
                    datetime.datetime.fromtimestamp(
                        filter.from_creation_date_utc
                    )
                )
            )
        if filter.to_completion_date_utc:
            where_clauses.append(
                TaskJob.completion_date.__le__(
                    datetime.datetime.fromtimestamp(
                        filter.to_completion_date_utc
                    )
                )
            )
        if filter.from_completion_date_utc:
            where_clauses.append(
                TaskJob.completion_date.__ge__(
                    datetime.datetime.fromtimestamp(
                        filter.from_completion_date_utc
                    )
                )
            )
        if filter.ref_id is not None:
            where_clauses.append(TaskJob.ref_id.__eq__(filter.ref_id))
        if len(filter.type) > 0:
            where_clauses.append(
                TaskJob.type.in_(
                    [task_type.value for task_type in filter.type]
                )
            )
        if len(where_clauses) > 1:
            query = query.where(
                TaskJobRepository._combine_clauses(where_clauses)
            )
        elif len(where_clauses) == 1:
            query = query.where(*where_clauses)

        tasks: List[TaskJob] = query.all()
        return tasks

    def delete(self, tid: str) -> None:
        task = db.session.get(TaskJob, tid)
        if task:
            db.session.delete(task)
            db.session.commit()
