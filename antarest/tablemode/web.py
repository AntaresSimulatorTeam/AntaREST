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
from http import HTTPStatus
from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter
from fastapi.params import Body, Depends
from pydantic import Field

from antarest.core.utils.web import APITag
from antarest.dependencies import TablemodeServiceDep, auth_required
from antarest.tablemode.model import TableColumn, TableModeDTO, TableType


def create_table_routes() -> APIRouter:
    bp = APIRouter(prefix="/v1", tags=[APITag.table_mode], dependencies=[Depends(auth_required)])

    @bp.post("/tablemode", summary="Define a new table the user wants to view", status_code=HTTPStatus.CREATED)
    def add_table(
        tablemode_service: TablemodeServiceDep,
        table_name: Annotated[str, Body(), Field(min_length=1, description="Table name cannot be empty")],
        table_type: Annotated[TableType, Body(), Field(description="Table type cannot be empty")],
        table_columns: Annotated[
            list[TableColumn], Body(), Field(min_length=1, description="At least one column is required")
        ],
    ) -> TableModeDTO:

        return tablemode_service.add_table(table_name=table_name, table_type=table_type, table_columns=table_columns)

    @bp.get("/tablemode", summary="Get Tables")
    def get_tables(tablemode_service: TablemodeServiceDep) -> List[TableModeDTO]:
        return tablemode_service.get_tables()

    @bp.put("/tablemode/{table_id}", summary="Update Tablemode")
    def update_table(
        tablemode_service: TablemodeServiceDep,
        table_id: UUID,
        table_type: Annotated[TableType, Body(), Field(description="Table type cannot be empty")],
        table_columns: Annotated[
            list[TableColumn], Body(), Field(min_length=1, description="At least one column is required")
        ],
    ) -> TableModeDTO:
        return tablemode_service.update_table(table_id=table_id, table_type=table_type, table_columns=table_columns)

    @bp.delete("/tablemode/{table_id}", summary="Delete Tablemode")
    def delete_table(tablemode_service: TablemodeServiceDep, table_id: UUID) -> None:
        tablemode_service.delete_table(table_id=table_id)

    return bp
