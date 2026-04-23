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

from sqlalchemy import ForeignKey, Integer, LargeBinary, PrimaryKeyConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.dbmodel import Base
from antarest.output.model import OutputVariablesList


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


class FileOutputRepository:
    """
    DB data for file output storage: stores variables list and variable views definitions.
    """

    def get_output_variables_list(self, study_id: str, output_id: str) -> OutputVariablesList | None:
        output_variables = db.session.get(DbOutputVariables, (study_id, output_id))
        return output_variables.to_model() if output_variables else None

    def save_output_variables_list(self, study_id: str, output_id: str, variables_list: OutputVariablesList) -> None:
        db_model = DbOutputVariables.from_model(study_id, output_id, variables_list)
        db.session.add(db_model)
        db.session.commit()
