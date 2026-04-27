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

    @bp.post("/tablemode", summary="Create a Tablemode")
    def add_tablemode(
        tablemode_service: TablemodeServiceDep,
        table_name: Annotated[str, Body(), Field(min_length=1, description="Table name cannot be empty")],
        table_type: Annotated[TableType, Body(), Field(description="Table type cannot be empty")],
        table_columns: Annotated[
            list[TableColumn], Body(), Field(min_length=1, description="At least one column is required")
        ],
    ) -> TableModeDTO:

        return tablemode_service.add_tablemode(
            table_name=table_name, table_type=table_type, table_columns=table_columns
        )

    @bp.get("/tablemode", summary="Get Tablemodes")
    def get_tablemodes(tablemode_service: TablemodeServiceDep) -> List[TableModeDTO]:
        return tablemode_service.get_tablemodes()

    @bp.put("/tablemode/{uuid}", summary="Update Tablemode")
    def update_tablemode(
        tablemode_service: TablemodeServiceDep,
        uuid: UUID,
        table_type: Annotated[TableType, Body(), Field(description="Table type cannot be empty")],
        table_columns: Annotated[
            list[TableColumn], Body(), Field(min_length=1, description="At least one column is required")
        ],
    ) -> TableModeDTO:
        return tablemode_service.update_tablemode(table_id=uuid, table_type=table_type, table_columns=table_columns)

    @bp.delete("/tablemode/{uuid}", summary="Delete Tablemode")
    def delete_tablemode(tablemode_service: TablemodeServiceDep, uuid: UUID) -> None:
        tablemode_service.delete_tablemode(table_id=uuid)

    return bp
