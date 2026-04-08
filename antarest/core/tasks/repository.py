# Copyright (c) 2026, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import datetime
from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from antarest.core.tasks.model import TaskJob, TaskListFilter
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import current_time


class TaskJobRepository:
    """
    Database connector to manage Tasks/Jobs entities.
    """

    @property
    def session(self) -> Session:
        """
        Get the SQLAlchemy session for the repository.

        Returns:
            SQLAlchemy session.
        """
        return db.session

    def save(self, task: TaskJob) -> TaskJob:
        session = self.session
        task = session.merge(task)
        session.add(task)
        session.commit()
        return task

    def get(self, id: str) -> TaskJob | None:
        session = self.session
        task: TaskJob | None = session.get(TaskJob, id)
        if task is not None:
            session.refresh(task)
        return task

    def get_or_raise(self, id: str) -> TaskJob:
        task = self.get(id)
        if task is None:
            raise HTTPException(HTTPStatus.NOT_FOUND, f"Task {id} not found")
        return task

    def list(self, filter: TaskListFilter, user: int | None = None) -> list[TaskJob]:
        stmt = select(TaskJob)
        if user:
            stmt = stmt.where(TaskJob.owner_id == user)
        if len(filter.status) > 0:
            _values = [status.value for status in filter.status]
            stmt = stmt.where(TaskJob.status.in_(_values))
        if filter.name:
            stmt = stmt.where(TaskJob.name.ilike(f"%{filter.name}%"))
        if filter.to_creation_date_utc:
            _date = datetime.datetime.fromtimestamp(filter.to_creation_date_utc)
            stmt = stmt.where(TaskJob.creation_date <= _date)
        if filter.from_creation_date_utc:
            _date = datetime.datetime.fromtimestamp(filter.from_creation_date_utc)
            stmt = stmt.where(TaskJob.creation_date >= _date)
        if filter.to_completion_date_utc:
            _date = datetime.datetime.fromtimestamp(filter.to_completion_date_utc)
            _clause = and_(TaskJob.completion_date.isnot(None), TaskJob.completion_date <= _date)
            stmt = stmt.where(_clause)
        if filter.from_completion_date_utc:
            _date = datetime.datetime.fromtimestamp(filter.from_completion_date_utc)
            _clause = and_(TaskJob.completion_date.isnot(None), TaskJob.completion_date >= _date)
            stmt = stmt.where(_clause)
        if filter.ref_id is not None:
            stmt = stmt.where(TaskJob.ref_id == filter.ref_id)
        if filter.type:
            _types = [task_type.value for task_type in filter.type]
            stmt = stmt.where(TaskJob.type.in_(_types))

        result = self.session.execute(stmt)
        tasks: list[TaskJob] = list(result.scalars().all())
        return tasks

    def delete(self, tid: str) -> None:
        session = self.session
        task = session.get(TaskJob, tid)
        if task:
            session.delete(task)
            session.commit()

    def delete_by_creation_date(self, task_retention_duration: int) -> int:
        session = self.session
        ctime = current_time()
        deleted_rows = (
            session.query(TaskJob)
            .filter(TaskJob.creation_date < ctime - datetime.timedelta(days=task_retention_duration))
            .delete()
        )
        session.commit()
        return deleted_rows
