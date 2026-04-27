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

from enum import StrEnum
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from antarest.core.persistence import Base
from antarest.core.serde import AntaresBaseModel


class TableType(StrEnum):
    """
    Table types.

    This enum is used to define the different types of tables that can be created
    by the user to leverage the editing capabilities of multiple objects at once.

    Attributes:
        AREA: Area table.
        LINK: Link table.
        THERMAL: Thermal clusters table.
        RENEWABLE: Renewable clusters table.
        ST_STORAGE: Short-Term Storages table.
        BINDING_CONSTRAINT: Binding constraints table.
    """

    AREA = "areas"
    LINK = "links"
    THERMAL = "thermals"
    RENEWABLE = "renewables"
    # Avoid "storages" because we may have "lt-storages" (long-term storages) in the future
    ST_STORAGE = "st-storages"
    # Avoid "constraints" because we may have other kinds of constraints in the future
    BINDING_CONSTRAINT = "binding-constraints"
    ST_STORAGE_ADDITIONAL_CONSTRAINTS = "st-storages-additional-constraints"


class TableColumn(StrEnum):
    AVERAGE_UNSUPPLIED_ENERGY_COST = "averageUnsuppliedEnergyCost"
    SPREAD_UNSUPPLIED_ENERGY_COST = "spreadUnsuppliedEnergyCost"
    AVERAGE_SPILLED_ENERGY_COST = "averageSpilledEnergyCost"
    SPREAD_SPILLED_ENERGY_COST = "spreadSpilledEnergyCost"
    NON_DISPATCHABLE_POWER = "nonDispatchablePower"
    DISPATCHABLE_HYDRO_POWER = "dispatchableHydroPower"
    OTHER_DISPATCHABLE_POWER = "otherDispatchablePower"


class TableMode(Base):
    __tablename__ = "tablemode"

    table_id: Mapped[UUID] = mapped_column(Uuid(), primary_key=True, nullable=False)
    table_name: Mapped[str] = mapped_column(String(255), nullable=False)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("identities.id", name="fk_user_id", ondelete="CASCADE"), nullable=False
    )
    table_type: Mapped[str] = mapped_column(String(255), nullable=False)
    table_columns: Mapped[str] = mapped_column(String(255), nullable=False)

    def to_dto(self) -> "TableModeDTO":
        return TableModeDTO(
            table_id=self.table_id,
            table_name=self.table_name,
            table_type=self.table_type,
            table_columns=self.table_columns.split(","),
        )


class TableModeDTO(AntaresBaseModel, extra="forbid"):
    table_id: UUID
    table_name: str
    table_type: str
    table_columns: list[str]
