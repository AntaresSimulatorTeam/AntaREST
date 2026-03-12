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

from sqlalchemy import Boolean, Column, ForeignKeyConstraint, Integer, String, Table, delete, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from antarest.core.persistence import Base
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.launcher.model import LogType
from antarest.output.output_model import OutputVariablesList
from antarest.study.dao.database.sql_utils import upsert_one


class DbOutputMetadataV2(Base):
    __tablename__ = "output_v2_metadata"

    # Design note: we don't enforce a foreign key constraint on study_id because it
    #              constrains too much the workflow, for example it does not allow
    #              to mark an output for deletion and delete it later, or just to
    #              delete output after deleting the study itself
    study_id: Mapped[str] = mapped_column(
        String(),
        primary_key=True,
        nullable=False,
    )
    output_name: Mapped[str] = mapped_column(String(), primary_key=True, nullable=False)
    archived: Mapped[bool] = mapped_column(Boolean(), nullable=False)
    # TODO: enum ?
    mode: Mapped[str] = mapped_column(String(), nullable=False)
    synthesis: Mapped[bool] = mapped_column(Boolean(), nullable=False)
    by_year: Mapped[bool] = mapped_column(Boolean(), nullable=False)
    nb_years: Mapped[int] = mapped_column(Integer(), nullable=False)

    # Definition of the 12-month range
    # TODO: enum
    start_month: Mapped[int] = mapped_column(Integer(), nullable=False)
    # TODO: enum
    january_first_weekday: Mapped[int] = mapped_column(Integer(), nullable=False)
    leap_year: Mapped[bool] = mapped_column(Boolean(), nullable=False)

    # Definition of the simulation range
    start_day: Mapped[int] = mapped_column(Integer(), nullable=False)
    end_day: Mapped[int] = mapped_column(Integer(), nullable=False)

    # For weekly aggregation
    # TODO: enum
    first_weekday: Mapped[int] = mapped_column(Integer(), nullable=False)


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


class DbOutputVariablesV2(Base):
    """
    Table for storing the list of variables of an output.
    The variables are actually stored as a JSON string which is compressed.

    Note that the only difference with the table used in v1 is the foreign key constraint on the output metadata.
    """

    __tablename__ = "output_v2_variables"
    __table_args__ = (
        ForeignKeyConstraint(
            ["study_id", "output_id"],
            ["output_v2_metadata.study_id", "output_v2_metadata.output_name"],
            ondelete="CASCADE",
        ),
    )

    study_id: Mapped[str] = mapped_column(String(36), nullable=False, primary_key=True)
    output_id: Mapped[str] = mapped_column(String(), nullable=False, primary_key=True)
    variables_list_version: Mapped[int] = mapped_column(Integer, nullable=False)
    variables_list: Mapped[str] = mapped_column(String(), nullable=False)

    def to_model(self) -> OutputVariablesList:
        return OutputVariablesList.model_validate_json(self.variables_list)

    @staticmethod
    def from_model(study_id: str, output_id: str, variables_list: OutputVariablesList) -> "DbOutputVariablesV2":
        return DbOutputVariablesV2(
            study_id=study_id,
            output_id=output_id,
            variables_list_version=1,
            variables_list=variables_list.model_dump_json(),
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
        return self.session.get(DbOutputMetadataV2, (study_id, output_name))

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

    def save_log(self, study_id: str, output_name: str, log_type: LogType, log_content: str) -> None:
        upsert_one(
            self.session,
            OUTPUT_LOGS_TABLE,
            values={"study_id": study_id, "output_id": output_name, _log_field_name(log_type): log_content},
        )
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

    def get_output_variables_list(self, study_id: str, output_id: str) -> OutputVariablesList | None:
        output_variables = self.session.get(DbOutputVariablesV2, (study_id, output_id))
        return output_variables.to_model() if output_variables else None

    def save_output_variables_list(self, study_id: str, output_id: str, variables_list: OutputVariablesList) -> None:
        db_model = DbOutputVariablesV2.from_model(study_id, output_id, variables_list)
        self.session.add(db_model)
        self.session.commit()
