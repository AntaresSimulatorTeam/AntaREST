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
import gzip

from pydantic import TypeAdapter
from sqlalchemy import ForeignKey, Integer, LargeBinary, PrimaryKeyConstraint, String, delete, insert, select
from sqlalchemy.orm import Mapped, mapped_column

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.dbmodel import Base
from antarest.output.model import OutputVariablesList
from antarest.output.model.gems_views import GemsTaxonomyViews

_GEMS_VIEWS_ADAPTER: TypeAdapter[list[GemsTaxonomyViews]] = TypeAdapter(list[GemsTaxonomyViews])


class DbOutputVariables(Base):
    """
    Table for storing the list of variables of an output.
    The variables are actually stored as a JSON string which is compressed.

    Note: we should not have compressed it in the application, postgresql handles compression itself.
    """

    __tablename__ = "output_variables"
    __table_args__ = (PrimaryKeyConstraint("study_id", "output_id"),)

    study_id: Mapped[str] = mapped_column(String(36), ForeignKey("study.id"), nullable=False)
    output_id: Mapped[str] = mapped_column(String, nullable=False)
    variables_list_version: Mapped[int] = mapped_column(Integer, nullable=False)
    variables_list: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    def to_model(self) -> OutputVariablesList:
        return OutputVariablesList.model_validate_json(gzip.decompress(self.variables_list))

    @staticmethod
    def from_model(study_id: str, output_id: str, variables_list: OutputVariablesList) -> "DbOutputVariables":
        compressed_content = gzip.compress(variables_list.model_dump_json().encode("utf-8"))
        return DbOutputVariables(
            study_id=study_id,
            output_id=output_id,
            variables_list_version=1,
            variables_list=compressed_content,
        )


class DbOutputGemsViews(Base):
    """
    Table for storing the GEMS views of an output, as a JSON string.

    Reading them from the output files is costly (every parquet file of the views is scanned),
    and an output never changes once written: they are computed once, then read from here.
    """

    __tablename__ = "output_gems_views"

    study_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("study.id", name="fk_output_gems_views_study_id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    output_id: Mapped[str] = mapped_column(String(), primary_key=True, nullable=False)
    views_version: Mapped[int] = mapped_column(Integer(), nullable=False)
    views: Mapped[str] = mapped_column(String(), nullable=False)


class FileOutputRepository:
    """
    DB data for file output storage: stores variables list, variable views definitions and GEMS views.
    """

    def get_output_variables_list(self, study_id: str, output_id: str) -> OutputVariablesList | None:
        output_variables = db.session.get(DbOutputVariables, (study_id, output_id))
        return output_variables.to_model() if output_variables else None

    def save_output_variables_list(self, study_id: str, output_id: str, variables_list: OutputVariablesList) -> None:
        db_model = DbOutputVariables.from_model(study_id, output_id, variables_list)
        db.session.add(db_model)
        db.session.commit()

    def get_output_gems_views(self, study_id: str, output_id: str) -> list[GemsTaxonomyViews] | None:
        """
        Returns the stored GEMS views of the output, or None if they are not stored.
        """
        stmt = select(DbOutputGemsViews.views).where(
            DbOutputGemsViews.study_id == study_id, DbOutputGemsViews.output_id == output_id
        )
        views = db.session.execute(stmt).scalar_one_or_none()
        return _GEMS_VIEWS_ADAPTER.validate_json(views) if views is not None else None

    def save_output_gems_views(self, study_id: str, output_id: str, views: list[GemsTaxonomyViews]) -> None:
        stmt = insert(DbOutputGemsViews).values(
            study_id=study_id,
            output_id=output_id,
            views_version=1,
            views=_GEMS_VIEWS_ADAPTER.dump_json(views).decode("utf-8"),
        )
        db.session.execute(stmt)
        db.session.commit()

    def delete_output_gems_views(self, study_id: str, output_id: str) -> None:
        stmt = delete(DbOutputGemsViews).where(
            DbOutputGemsViews.study_id == study_id, DbOutputGemsViews.output_id == output_id
        )
        db.session.execute(stmt)
        db.session.commit()
