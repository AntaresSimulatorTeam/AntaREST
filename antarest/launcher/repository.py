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

import logging
from typing import List, Optional

from sqlalchemy import delete, select

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.launcher.model import JobResult, LaunchConfigModel
from antarest.study.model import Study

logger = logging.getLogger(__name__)


class JobResultRepository:
    def __init__(self) -> None:
        pass

    def save(self, job: JobResult) -> JobResult:
        logger.debug(f"Saving JobResult {job.id}")

        stmt = select(JobResult).where(JobResult.id == job.id)
        existing_job = db.session.scalar(stmt)

        if existing_job:
            merged_job = db.session.merge(job)
        else:
            db.session.add(job)
            merged_job = job

        db.session.commit()
        return merged_job

    def save_all(self, jobs: List[JobResult]) -> None:
        logger.debug(f"Saving {len(jobs)} new JobResults")
        db.session.add_all(jobs)
        db.session.commit()

    def get(self, id: str) -> Optional[JobResult]:
        logger.debug(f"Retrieving JobResult {id}")
        return db.session.get(JobResult, id)

    def get_all(self, filter_orphan: bool = False, latest: Optional[int] = None) -> List[JobResult]:
        logger.debug("Retrieving all JobResults")

        stmt = select(JobResult)
        if filter_orphan:
            stmt = stmt.join(Study, JobResult.study_id == Study.id)

        stmt = stmt.order_by(JobResult.creation_date.desc())

        if latest:
            stmt = stmt.limit(latest)

        return list(db.session.scalars(stmt).all())

    def get_running(self) -> List[JobResult]:
        stmt = select(JobResult).where(JobResult.completion_date.is_(None))
        return list(db.session.scalars(stmt).all())

    def find_by_study(self, study_id: str) -> List[JobResult]:
        logger.debug(f"Retrieving JobResults from study {study_id}")
        stmt = select(JobResult).where(JobResult.study_id == study_id)
        return list(db.session.scalars(stmt).all())

    def find_by_study_and_output_ids(self, study_id: str, output_ids: List[str]) -> List[JobResult]:
        logger.debug(f"Retrieving JobResults from study {study_id}")
        stmt = select(JobResult).where(JobResult.study_id == study_id).where(JobResult.output_id.in_(output_ids))
        return list(db.session.scalars(stmt).all())

    def delete(self, id: str) -> None:
        logger.debug(f"Deleting JobResult {id}")
        g = db.session.get(JobResult, id)
        db.session.delete(g)
        db.session.commit()

    def delete_by_study_id(self, study_id: str) -> None:
        logger.debug(f"Deleting JobResults from_study {study_id}")
        stmt = delete(JobResult).where(JobResult.study_id == study_id)
        db.session.execute(stmt)
        db.session.commit()


class LaunchConfigRepository:
    def __init__(self) -> None:
        pass

    def exists(self, id: str) -> bool:
        logger.debug(f"Checking existence of LaunchConfigModel {id}")
        stmt = select(LaunchConfigModel).where(LaunchConfigModel.id == id)
        existing_config = db.session.scalar(stmt)
        return existing_config is not None

    def save(self, config: LaunchConfigModel) -> LaunchConfigModel:
        logger.debug(f"Saving LaunchConfigModel {config.id}")

        stmt = select(LaunchConfigModel).where(LaunchConfigModel.id == config.id)
        existing_config = db.session.scalar(stmt)

        if existing_config:
            merged_config = db.session.merge(config)
        else:
            db.session.add(config)
            merged_config = config

        db.session.commit()
        return merged_config

    def get(self, id: str) -> Optional[LaunchConfigModel]:
        logger.debug(f"Retrieving LaunchConfigModel {id}")
        return db.session.get(LaunchConfigModel, id)

    def get_all(self) -> List[LaunchConfigModel]:
        logger.debug("Retrieving all LaunchConfigModels")
        stmt = select(LaunchConfigModel)
        return list(db.session.scalars(stmt).all())

    def delete(self, id: str) -> None:
        logger.debug(f"Deleting LaunchConfigModel {id}")
        config = db.session.get(LaunchConfigModel, id)
        if config:
            db.session.delete(config)
            db.session.commit()
