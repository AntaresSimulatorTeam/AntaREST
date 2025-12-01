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
from antarest.launcher.model import JobResult, SolverPresetsDB
from antarest.study.model import Study

logger = logging.getLogger(__name__)


class JobResultRepository:
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


class SolverPresetsRepository:
    def save(self, solver_presets_db: SolverPresetsDB) -> SolverPresetsDB:
        logger.debug(f"Saving SolverPresetsModel {solver_presets_db.id}")

        stmt = select(SolverPresetsDB).where(SolverPresetsDB.id == solver_presets_db.id)
        existing_config = db.session.scalar(stmt)

        if existing_config:
            merged_config = db.session.merge(solver_presets_db)
        else:
            db.session.add(solver_presets_db)
            merged_config = solver_presets_db

        db.session.commit()
        return merged_config

    def get(self, id: str) -> Optional[SolverPresetsDB]:
        logger.debug(f"Retrieving SolverPresetsModel {id}")
        return db.session.get(SolverPresetsDB, id)

    def get_all(self) -> List[SolverPresetsDB]:
        logger.debug("Retrieving all SolverPresetsModel")
        stmt = select(SolverPresetsDB)
        return list(db.session.scalars(stmt).all())

    def delete(self, id: str) -> None:
        logger.debug(f"Deleting SolverPresetsModel {id}")
        stmt = delete(SolverPresetsDB).where(SolverPresetsDB.id == id)
        db.session.execute(stmt)
        db.session.commit()
