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

from datetime import datetime
from typing import cast

from sqlalchemy import Table, delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.sql_utils import upsert_one
from antarest.output.dbmodel import Output


class OutputRepository:
    def __init__(self, session: Session | None = None):
        self._session = session

    @property
    def session(self) -> Session:
        if self._session is None:
            return db.session
        return self._session

    def save(self, output_metadata: Output) -> Output:
        session = self.session
        output = session.merge(output_metadata)
        session.commit()
        return output

    def get(self, study_id: str, output_id: str) -> Output | None:
        stmt = select(Output).where((Output.output_id == output_id) & (Output.study_id == study_id))
        result = self.session.execute(stmt.execution_options(populate_existing=True))
        return result.unique().scalar_one_or_none()

    def initialize(self, study_id: str, output_id: str, last_access: datetime, archived: bool) -> None:
        session = self.session
        if self.get(study_id, output_id) is None:
            try:
                session.add(Output(study_id=study_id, output_id=output_id, last_access=last_access, archived=archived))
                session.commit()
                return
            except IntegrityError:
                session.rollback()
                # Another session may have created the output since the lookup.
                if self.get(study_id, output_id) is None:
                    raise

        stmt = (
            update(Output)
            .where(Output.study_id == study_id, Output.output_id == output_id)
            .values(
                last_access=func.coalesce(Output.last_access, last_access),
                archived=func.coalesce(Output.archived, archived),
            )
        )
        session.execute(stmt)
        session.commit()

    def update_last_access(self, study_id: str, output_id: str, last_access: datetime) -> None:
        stmt = (
            update(Output)
            .where(
                Output.study_id == study_id,
                Output.output_id == output_id,
                (Output.last_access.is_(None)) | (Output.last_access < last_access),
            )
            .values(last_access=last_access)
        )
        self.session.execute(stmt)
        self.session.commit()

    def update_archived(self, study_id: str, output_id: str, archived: bool) -> None:
        stmt = (
            update(Output)
            .where(Output.study_id == study_id, Output.output_id == output_id)
            .values(archived=archived, disk_space_bytes=None)
        )
        self.session.execute(stmt)
        self.session.commit()

    def save_disk_usage(self, study_id: str, output_id: str, disk_space_bytes: int) -> None:
        upsert_one(
            self.session,
            cast(Table, Output.__table__),
            {"study_id": study_id, "output_id": output_id, "disk_space_bytes": disk_space_bytes},
        )
        self.session.commit()

    def invalidate_disk_usage(self, study_id: str, output_id: str) -> None:
        stmt = (
            update(Output)
            .where(Output.study_id == study_id, Output.output_id == output_id)
            .values(disk_space_bytes=None)
        )
        self.session.execute(stmt)
        self.session.commit()

    def get_outputs_to_archive(self, study_id: str, cutoff: datetime) -> list[Output]:
        stmt = (
            select(Output)
            .where(Output.study_id == study_id, Output.archived.is_(False), Output.last_access <= cutoff)
            .order_by(Output.output_id)
            .execution_options(populate_existing=True)
        )
        return list(self.session.scalars(stmt))

    def get_output_ids(self, study_id: str) -> list[str]:
        stmt = select(Output.output_id).where(Output.study_id == study_id)
        return list(self.session.scalars(stmt))

    def has_outputs_to_preserve(self, study_id: str, cutoff: datetime) -> bool:
        stmt = (
            select(Output.output_id)
            .where(Output.study_id == study_id, (Output.archived.is_(False)) | (Output.last_access > cutoff))
            .limit(1)
        )
        return self.session.scalar(stmt) is not None

    def delete(self, study_id: str, output_id: str) -> None:

        session = self.session
        stmt = delete(Output).where(Output.output_id == output_id).where(Output.study_id == study_id)

        session.execute(stmt)
        session.commit()
