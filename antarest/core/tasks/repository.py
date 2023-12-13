import datetime
import typing as t
from http import HTTPStatus
from operator import and_

from fastapi import HTTPException
from sqlalchemy.orm import Session  # type: ignore

from antarest.core.tasks.model import TaskJob, TaskListFilter, TaskStatus
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import assert_this


class TaskJobRepository:
    """
    Database connector to manage Tasks/Jobs entities.
    """

    def __init__(self, session: t.Optional[Session] = None):
        """
        Initialize the repository.

        Args:
            session: Optional SQLAlchemy session to be used.
        """
        self._session = session

    @property
    def session(self) -> Session:
        """
        Get the SQLAlchemy session for the repository.

        Returns:
            SQLAlchemy session.
        """
        if self._session is None:
            # Get or create the session from a context variable (thread local variable)
            return db.session
        # Get the user-defined session
        return self._session

    def save(self, task: TaskJob) -> TaskJob:
        session = self.session
        task = session.merge(task)
        session.add(task)
        session.commit()
        return task

    def get(self, id: str) -> t.Optional[TaskJob]:
        session = self.session
        task: TaskJob = session.get(TaskJob, id)
        if task is not None:
            session.refresh(task)
        return task

    def get_or_raise(self, id: str) -> TaskJob:
        task = self.get(id)
        if task is None:
            raise HTTPException(HTTPStatus.NOT_FOUND, f"Task {id} not found")
        return task

    @staticmethod
    def _combine_clauses(where_clauses: t.List[t.Any]) -> t.Any:
        assert_this(len(where_clauses) > 0)
        if len(where_clauses) > 1:
            return and_(
                where_clauses[0],
                TaskJobRepository._combine_clauses(where_clauses[1:]),
            )
        else:
            return where_clauses[0]

    def list(self, filter: TaskListFilter, user: t.Optional[int] = None) -> t.List[TaskJob]:
        query = self.session.query(TaskJob)
        where_clauses: t.List[t.Any] = []
        if user:
            where_clauses.append(TaskJob.owner_id == user)
        if len(filter.status) > 0:
            where_clauses.append(TaskJob.status.in_([status.value for status in filter.status]))
        if filter.name:
            where_clauses.append(TaskJob.name.ilike(f"%{filter.name}%"))
        if filter.to_creation_date_utc:
            where_clauses.append(
                TaskJob.creation_date.__le__(datetime.datetime.fromtimestamp(filter.to_creation_date_utc))
            )
        if filter.from_creation_date_utc:
            where_clauses.append(
                TaskJob.creation_date.__ge__(datetime.datetime.fromtimestamp(filter.from_creation_date_utc))
            )
        if filter.to_completion_date_utc:
            where_clauses.append(
                TaskJob.completion_date.__le__(datetime.datetime.fromtimestamp(filter.to_completion_date_utc))
            )
        if filter.from_completion_date_utc:
            where_clauses.append(
                TaskJob.completion_date.__ge__(datetime.datetime.fromtimestamp(filter.from_completion_date_utc))
            )
        if filter.ref_id is not None:
            where_clauses.append(TaskJob.ref_id.__eq__(filter.ref_id))
        if len(filter.type) > 0:
            where_clauses.append(TaskJob.type.in_([task_type.value for task_type in filter.type]))
        if len(where_clauses) > 1:
            query = query.where(TaskJobRepository._combine_clauses(where_clauses))
        elif len(where_clauses) == 1:
            query = query.where(*where_clauses)

        tasks: t.List[TaskJob] = query.all()
        return tasks

    def delete(self, tid: str) -> None:
        session = self.session
        task = session.get(TaskJob, tid)
        if task:
            session.delete(task)
            session.commit()

    def update_timeout(self, task_id: str, timeout: int) -> None:
        """Update task status to TIMEOUT."""
        session = self.session
        task: TaskJob = session.get(TaskJob, task_id)
        task.status = TaskStatus.TIMEOUT
        task.result_msg = f"Task '{task_id}' timeout after {timeout} seconds"
        task.result_status = False
        session.commit()
