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
from typing import Iterator

from sqlalchemy import Column, ForeignKeyConstraint, String, Table, delete, select
from sqlalchemy.orm import Mapped, mapped_column

from antarest.core.persistence import Base
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.launcher.model import LogType
from antarest.study.dao.database.sql_utils import upsert_one


class DbOutputMetadata(Base):
    __tablename__ = "output_metadata"

    # Design note: we don't enforce a foreign key constraint on study_id because it
    #              constrains too much the workflow, for example it does not allow
    #              to mark an output for deletion and delete it later, or just to
    #              delete output after deleting the study itself
    study_id: Mapped[str] = mapped_column(
        primary_key=True,
        nullable=False,
    )
    output_name: Mapped[str] = mapped_column(primary_key=True, nullable=False)
    archived: Mapped[bool] = mapped_column(nullable=False)
    # TODO: enum ?
    mode: Mapped[str] = mapped_column(nullable=False)
    synthesis: Mapped[bool] = mapped_column(nullable=False)
    by_year: Mapped[bool] = mapped_column(nullable=False)
    nb_years: Mapped[int] = mapped_column(nullable=False)


OUTPUT_LOGS_TABLE = Table(
    "output_logs",
    Base.metadata,
    Column("study_id", String(), primary_key=True, nullable=False),
    Column("output_id", String(), primary_key=True, nullable=False),
    Column("out", String(), nullable=True),
    Column("err", String(), nullable=True),
    ForeignKeyConstraint(
        ["study_id", "output_id"], ["output_metadata.study_id", "output_metadata.output_name"], ondelete="CASCADE"
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


class OutputRepository:
    """
    Provides access to output data.
    """

    def get(self, study_id: str, output_name: str) -> DbOutputMetadata | None:
        return db.session.get(DbOutputMetadata, (study_id, output_name))

    def get_all(self, study_id: str | None = None, archived: bool | None = None) -> Iterator[DbOutputMetadata]:
        stmt = select(DbOutputMetadata)
        if study_id is not None:
            stmt = stmt.where(DbOutputMetadata.study_id == study_id)
        if archived is not None:
            stmt = stmt.where(DbOutputMetadata.archived == archived)
        return db.session.scalars(stmt)

    def delete(self, study_id: str, output_name: str) -> None:
        stmt = delete(DbOutputMetadata).where(
            DbOutputMetadata.study_id == study_id, DbOutputMetadata.output_name == output_name
        )
        db.session.execute(stmt)
        db.session.commit()

    def save_log(self, study_id: str, output_name: str, log_type: LogType, log_content: str) -> None:
        upsert_one(
            db.session,
            OUTPUT_LOGS_TABLE,
            values={"study_id": study_id, "output_id": output_name, _log_field_name(log_type): log_content},
        )
        db.session.commit()

    def save(self, output_metadata: DbOutputMetadata) -> None:
        db.session.add(output_metadata)
        db.session.commit()

    def get_log(self, study_id: str, output_name: str, log_type: LogType) -> str:
        stmt = select(OUTPUT_LOGS_TABLE.c[_log_field_name(log_type)]).where(
            OUTPUT_LOGS_TABLE.c.study_id == study_id, OUTPUT_LOGS_TABLE.c.output_id == output_name
        )
        res = db.session.execute(stmt)
        return res.scalars().first() or ""
