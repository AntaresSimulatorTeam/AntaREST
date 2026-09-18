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
from collections.abc import Iterator

from sqlalchemy import Column, ForeignKeyConstraint, String, Table, delete, select
from sqlalchemy.orm import Session

from antarest.core.persistence import Base
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.sql_utils import upsert_one
from antarest.launcher.model import LogType
from antarest.output.storage.v2.dbmodel import DbOutputMetadataV2 as DbOutputMetadataV2

OUTPUT_LOGS_TABLE = Table(
    "output_v2_logs",
    Base.metadata,
    Column("study_id", String(), primary_key=True, nullable=False),
    Column("output_id", String(), primary_key=True, nullable=False),
    Column("out", String(), nullable=True),
    Column("err", String(), nullable=True),
    ForeignKeyConstraint(
        ["study_id", "output_id"], ["output_v2_metadata.study_id", "output_v2_metadata.output_name"], ondelete="CASCADE"
    ),
)


def _log_field_name(log_type: LogType) -> str:
    match log_type:
        case LogType.STDOUT:
            return "out"
        case LogType.STDERR:
            return "err"
        case _:
            raise ValueError(f"Unknown log type: {log_type}")


class OutputV2Repository:
    """
    Provides access to output data for output storage v2.

    There is quite some duplication from file output storage repository which already stored some data in database,
    but I prefer here to have a real separation between the 2 implementations.
    """

    @property
    def session(self) -> Session:
        return db.session

    def get_output_metadata(self, study_id: str, output_name: str) -> DbOutputMetadataV2 | None:
        return self.session.scalar(
            select(DbOutputMetadataV2).where(
                DbOutputMetadataV2.study_id == study_id, DbOutputMetadataV2.output_name == output_name
            )
        )

    def search_output_metadata(
        self, study_id: str | None = None, archived: bool | None = None
    ) -> Iterator[DbOutputMetadataV2]:
        stmt = select(DbOutputMetadataV2)
        if study_id is not None:
            stmt = stmt.where(DbOutputMetadataV2.study_id == study_id)
        if archived is not None:
            stmt = stmt.where(DbOutputMetadataV2.archived == archived)
        return self.session.scalars(stmt)

    def delete_output(self, study_id: str, output_name: str) -> None:
        stmt = delete(DbOutputMetadataV2).where(
            DbOutputMetadataV2.study_id == study_id, DbOutputMetadataV2.output_name == output_name
        )
        self.session.execute(stmt)
        self.session.commit()

    def save_log(
        self, study_id: str, output_name: str, log_type: LogType, log_content: str, *, commit: bool = True
    ) -> None:
        upsert_one(
            self.session,
            OUTPUT_LOGS_TABLE,
            values={"study_id": study_id, "output_id": output_name, _log_field_name(log_type): log_content},
        )
        if commit:
            self.session.commit()

    def save_output_metadata(self, output_metadata: DbOutputMetadataV2) -> None:
        self.session.add(output_metadata)
        self.session.commit()

    def get_log(self, study_id: str, output_name: str, log_type: LogType) -> str:
        stmt = select(OUTPUT_LOGS_TABLE.c[_log_field_name(log_type)]).where(
            OUTPUT_LOGS_TABLE.c.study_id == study_id, OUTPUT_LOGS_TABLE.c.output_id == output_name
        )
        res = self.session.execute(stmt)
        return res.scalars().first() or ""
