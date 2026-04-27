import http
from uuid import UUID, uuid4

from fastapi import HTTPException

from antarest.login.utils import get_user_impersonator
from antarest.tablemode.model import TableColumn, TableMode, TableModeDTO, TableType
from antarest.tablemode.repository import TablemodeRepository


def _check_valid_data(table_columns: list[TableColumn], table_type: str) -> None:
    """
    Check the imput datas entered. Raise an exception if they don't match the values of the enums
    Args:
        table_columns: the input columns to check
        table_type: type of the table to check

    """
    type_list = [e.value for e in TableType]
    columns = [e.value for e in TableColumn]

    # check if table_type or table columns are not in the enums
    if table_type not in type_list:
        raise HTTPException(status_code=http.HTTPStatus.BAD_REQUEST, detail=f"Invalid table type: {table_type}")

    if not all(col in columns for col in table_columns):
        raise HTTPException(
            status_code=http.HTTPStatus.BAD_REQUEST, detail="Invalid table columns: " + ", ".join(table_columns)
        )


class TablemodeService:
    def __init__(self, tablemode_repository: TablemodeRepository):
        self.tablemode_repository = tablemode_repository

    def get_tablemodes(self) -> list[TableModeDTO]:
        tablemodes = self.tablemode_repository.get_all()
        tablemode_dtos = [tablemode.to_dto() for tablemode in tablemodes]
        return tablemode_dtos

    def add_tablemode(self, table_name: str, table_type: str, table_columns: list[TableColumn]) -> TableModeDTO:
        str_table_columns = ",".join(table_columns)
        _check_valid_data(table_columns, table_type)
        tablemode = TableMode(
            table_id=uuid4(),
            table_name=table_name,
            table_type=table_type,
            table_columns=str_table_columns,
            user_id=get_user_impersonator(),
        )

        tablemode_dto = self.tablemode_repository.save(tablemode).to_dto()

        return tablemode_dto

    def update_tablemode(self, table_id: UUID, table_type: TableType, table_columns: list[TableColumn]) -> TableModeDTO:
        """
        Update a selected tablemode's type and columns
        Args:
            table_id:
            table_type:
            table_columns:

        Returns:
            None
        """
        _check_valid_data(table_columns, table_type)

        tablemode = self.tablemode_repository.get(table_id)

        if not tablemode:
            raise HTTPException(
                status_code=http.HTTPStatus.NOT_FOUND, detail=f"Tablemode with id {table_id} not found"
            ) from None

        str_table_columns = ",".join(table_columns)

        tablemode.table_type = table_type
        tablemode.table_columns = str_table_columns

        updated_tablemode = self.tablemode_repository.save(tablemode)
        return updated_tablemode.to_dto()

    def delete_tablemode(self, table_id: UUID) -> None:
        tablemode = self.tablemode_repository.get(table_id)

        if tablemode:
            self.tablemode_repository.delete(table_id)
        else:
            raise HTTPException(
                status_code=http.HTTPStatus.NOT_FOUND, detail=f"tablemode with id {table_id} not found"
            ) from None
