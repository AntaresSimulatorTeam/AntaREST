import datetime
from operator import and_
from typing import Optional, List

from antarest.core.tasks.model import TaskJob, TaskListFilter
from antarest.core.utils.fastapi_sqlalchemy import db


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

    def list(
        self, filter: TaskListFilter, user: Optional[int] = None
    ) -> List[TaskJob]:
        query = db.session.query(TaskJob)
        where_clauses = []
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
        if len(where_clauses) > 1:
            query = query.where(and_(*where_clauses))
        elif len(where_clauses) == 1:
            query = query.where(*where_clauses)

        tasks: List[TaskJob] = query.all()
        return tasks

    def delete(self, tid: str) -> None:
        task = db.session.get(TaskJob, tid)
        if task:
            db.session.delete(task)
            db.session.commit()
