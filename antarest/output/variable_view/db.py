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
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, String, select
from sqlalchemy.orm import Mapped, mapped_column

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import current_time
from antarest.dbmodel import Base
from antarest.output.model import OutputVariablesType
from antarest.output.variable_view.model import (
    AreaOutputId,
    LinkOutputId,
    OutputItemId,
    RenewableClusterOutputId,
    ShortTermStorageOutputId,
    ThermalClusterOutputId,
)
from antarest.study.model import MatrixFrequency


class OutputVariablesViewsModel(Base):
    """
    Table for storing the definition of variable views which have been generated.
    """

    __tablename__ = "output_variables_views"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), unique=True)

    # TODO: check alembic migration for the ondelete cascade, otherwise we could be unable to delete some studies
    study_id: Mapped[str] = mapped_column(String(36), ForeignKey("study.id", ondelete="CASCADE"), nullable=False)
    output_id: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[OutputVariablesType] = mapped_column(Enum(OutputVariablesType), nullable=False)
    frequency: Mapped[MatrixFrequency] = mapped_column(Enum(MatrixFrequency), nullable=False)
    variable_name: Mapped[str] = mapped_column(String, nullable=False)
    area_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    area_from_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    area_to_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    thermal_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    renewable_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    st_storage_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    matrix_id: Mapped[str] = mapped_column(String, ForeignKey("matrix.id"), nullable=False)
    last_read: Mapped[datetime] = mapped_column(DateTime)


def get_output_view_inside_db(
    study_id: str,
    output_id: str,
    variable_name: str,
    frequency: MatrixFrequency,
    item_id: OutputItemId,
) -> OutputVariablesViewsModel | None:
    stmt = select(OutputVariablesViewsModel)
    stmt = stmt.where(OutputVariablesViewsModel.study_id == study_id)
    stmt = stmt.where(OutputVariablesViewsModel.output_id == output_id)
    stmt = stmt.where(OutputVariablesViewsModel.type == item_id.type)
    stmt = stmt.where(OutputVariablesViewsModel.frequency == frequency)
    stmt = stmt.where(OutputVariablesViewsModel.variable_name == variable_name)

    match item_id:
        case AreaOutputId():
            filters = [(OutputVariablesViewsModel.area_id, item_id.area_id)]
        case ThermalClusterOutputId():
            filters = [
                (OutputVariablesViewsModel.area_id, item_id.area_id),
                (OutputVariablesViewsModel.thermal_id, item_id.thermal_id),
            ]
        case RenewableClusterOutputId():
            filters = [
                (OutputVariablesViewsModel.area_id, item_id.area_id),
                (OutputVariablesViewsModel.renewable_id, item_id.renewable_id),
            ]
        case ShortTermStorageOutputId():
            filters = [
                (OutputVariablesViewsModel.area_id, item_id.area_id),
                (OutputVariablesViewsModel.st_storage_id, item_id.st_storage_id),
            ]
        case LinkOutputId():
            filters = [
                (OutputVariablesViewsModel.area_from_id, item_id.area_from_id),
                (OutputVariablesViewsModel.area_to_id, item_id.area_to_id),
            ]
        case _:
            raise NotImplementedError(f"output identifier `{item_id.__class__}` is not implemented")

    for column, value in filters:
        stmt = stmt.where(column == value)

    return db.session.scalar(stmt)


def create_output_view_db_model(
    study_id: str,
    output_id: str,
    variable_name: str,
    frequency: MatrixFrequency,
    output_identifier: OutputItemId,
    matrix_id: str,
) -> OutputVariablesViewsModel:
    model = OutputVariablesViewsModel(
        study_id=study_id,
        output_id=output_id,
        type=output_identifier.type,
        frequency=frequency,
        variable_name=variable_name,
        matrix_id=matrix_id,
        last_read=current_time(),
    )

    match output_identifier:
        case AreaOutputId():
            model.area_id = output_identifier.area_id
        case ThermalClusterOutputId():
            model.area_id = output_identifier.area_id
            model.thermal_id = output_identifier.thermal_id
        case RenewableClusterOutputId():
            model.area_id = output_identifier.area_id
            model.renewable_id = output_identifier.renewable_id
        case ShortTermStorageOutputId():
            model.area_id = output_identifier.area_id
            model.st_storage_id = output_identifier.st_storage_id
        case LinkOutputId():
            model.area_from_id = output_identifier.area_from_id
            model.area_to_id = output_identifier.area_to_id
        case _:
            raise NotImplementedError(f"output identifier `{output_identifier.__class__}` is not implemented")

    return model
