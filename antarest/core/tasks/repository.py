# Copyright (c) 2025, RTE (https://www.rte-france.com)
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
from operator import and_
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session 

from antarest.core.tasks.model import TaskJob, TaskListFilter
from antarest.core.utils.fastapi_sqlalchemy import db


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

    def get(self, id: str) -> Optional[TaskJob]:
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

    def list(self, filter: TaskListFilter, user: Optional[int] = None) -> List[TaskJob]:
        q = self.session.query(TaskJob)
        if user:
            q = q.filter(TaskJob.owner_id == user)
        if len(filter.status) > 0:
            _values = [status.value for status in filter.status]
            q = q.filter(TaskJob.status.in_(_values))  # type: ignore
        if filter.name:
            q = q.filter(TaskJob.name.ilike(f"%{filter.name}%"))  # type: ignore
        if filter.to_creation_date_utc:
            _date = datetime.datetime.fromtimestamp(filter.to_creation_date_utc)
            q = q.filter(TaskJob.creation_date <= _date)
        if filter.from_creation_date_utc:
            _date = datetime.datetime.fromtimestamp(filter.from_creation_date_utc)
            q = q.filter(TaskJob.creation_date >= _date)
        if filter.to_completion_date_utc:
            _date = datetime.datetime.fromtimestamp(filter.to_completion_date_utc)
            _clause = and_(TaskJob.completion_date.isnot(None), TaskJob.completion_date <= _date)  # type: ignore
            q = q.filter(_clause)
        if filter.from_completion_date_utc:
            _date = datetime.datetime.fromtimestamp(filter.from_completion_date_utc)
            _clause = and_(TaskJob.completion_date.isnot(None), TaskJob.completion_date >= _date)  # type: ignore
            q = q.filter(_clause)
        if filter.ref_id is not None:
            q = q.filter(TaskJob.ref_id == filter.ref_id)
        if filter.type:
            _types = [task_type.value for task_type in filter.type]
            q = q.filter(TaskJob.type.in_(_types))  # type: ignore
        tasks: List[TaskJob] = q.all()
        return tasks

    def delete(self, tid: str) -> None:
        session = self.session
        task = session.get(TaskJob, tid)
        if task:
            session.delete(task)
            session.commit()
