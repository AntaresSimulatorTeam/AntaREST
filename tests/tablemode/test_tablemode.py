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
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.login.utils import current_user_context
from antarest.tablemode.model import (
    AreaColumn,
    LinkColumn,
    STStorageColumn,
    TableMode,
    TableModeDTO,
    TableType,
    ThermalColumn,
)
from antarest.tablemode.repository import TablemodeRepository
from antarest.tablemode.service import TableModeService


def test_get_table_mode():
    # ensuring that the tablemode service returns an empty list when the tablemode repository returns an empty list
    mock_tablemode_repo = Mock(spec=TablemodeRepository)
    mock_tablemode_repo.get_all.return_value = []
    tablemode_service = TableModeService(mock_tablemode_repo)
    tablemode_list = tablemode_service.get_tables()
    assert tablemode_list == []

    # ensuring that the tablemode service returns a list of tablemodes when the tablemode repository returns a list of tablemodes
    mock_tablemode_repo = Mock(spec=TablemodeRepository)
    my_uuid = uuid.uuid4()
    my_table_name = "test_name"
    my_table_type = TableType.AREA
    area_col = AreaColumn.NON_DISPATCHABLE_POWER
    mock_tablemode_repo.get_all.return_value = [
        TableMode(
            table_id=my_uuid,
            table_name=my_table_name,
            table_type=my_table_type,
            table_columns=area_col,
            user_id=1,
        )
    ]
    tablemode_service = TableModeService(mock_tablemode_repo)
    tablemode_list = tablemode_service.get_tables()
    assert len(tablemode_list) == 1
    expected_dto = TableModeDTO(
        table_id=my_uuid, table_name=my_table_name, table_type=my_table_type, table_columns=[area_col]
    )
    assert tablemode_list[0] == expected_dto


def test_add_tablemode_success():
    mock_tablemode_repo = Mock(spec=TablemodeRepository)
    my_uuid = uuid.uuid4()
    table_name = "test_name"
    table_type = TableType.AREA
    table_columns = [AreaColumn.DISPATCHABLE_HYDRO_POWER, AreaColumn.NON_DISPATCHABLE_POWER]
    str_table_columns = ",".join(table_columns)
    tablemode_dto = TableModeDTO(
        table_id=my_uuid, table_name=table_name, table_type=table_type, table_columns=table_columns
    )

    tablemode = TableMode(
        table_id=my_uuid, table_name=table_name, table_type=table_type, table_columns=str_table_columns, user_id=1
    )
    mock_tablemode_repo.save.return_value = tablemode
    tablemode_service = TableModeService(mock_tablemode_repo)

    with current_user_context(DEFAULT_ADMIN_USER):
        tablemode_service.add_table(table_name, table_type, table_columns)

    mock_tablemode_repo.save.assert_called_once()
    call_arg = mock_tablemode_repo.save.call_args[0][0]
    assert call_arg.table_name == table_name
    assert call_arg.table_type == table_type
    assert call_arg.table_columns == str_table_columns

    mock_tablemode_repo.get_all.return_value = [tablemode]

    with current_user_context(DEFAULT_ADMIN_USER):
        current_tablemodes = tablemode_service.get_tables()

    assert current_tablemodes == [tablemode_dto]


def test_delete_tablemode_success():
    mock_tablemode_repo = Mock(spec=TablemodeRepository)
    my_uuid = uuid.uuid4()

    deleted_table_name = "test_name"
    deleted_table_type = TableType.AREA
    deleted_table_columns = [AreaColumn.DISPATCHABLE_HYDRO_POWER, LinkColumn.ASSET_TYPE]
    tablemode_service = TableModeService(mock_tablemode_repo)
    mock_tablemode_repo.get.return_value = TableMode(
        table_id=my_uuid,
        table_name=deleted_table_name,
        table_type=deleted_table_type,
        table_columns=",".join(deleted_table_columns),
    )
    tablemode_service.delete_table(my_uuid)
    mock_tablemode_repo.delete.assert_called_once()

    mock_tablemode_repo.get_all.return_value = []

    assert tablemode_service.get_tables() == []


def test_update_tablemode_success():
    mock_tablemode_repo = Mock(spec=TablemodeRepository)
    my_uuid = uuid.uuid4()
    table_name = "test_name"
    current_table_type = TableType.AREA
    current_table_columns = [AreaColumn.DISPATCHABLE_HYDRO_POWER, AreaColumn.OTHER_DISPATCHABLE_POWER]

    update_table_type = TableType.ST_STORAGE

    str_tables = ",".join(current_table_columns)
    update_table_columns = [STStorageColumn.EFFICIENCY]
    str_updated_table = ",".join(update_table_columns)

    tablemode_service = TableModeService(mock_tablemode_repo)

    # updating the table type and table columns together
    mock_tablemode_repo.get.return_value = TableMode(
        table_id=my_uuid, table_name=table_name, table_type=current_table_type, table_columns=str_tables
    )
    mock_tablemode_repo.save.return_value = TableMode(
        table_id=my_uuid, table_name=table_name, table_type=update_table_type, table_columns=str_updated_table
    )
    updated_dto = tablemode_service.update_table(my_uuid, update_table_type, update_table_columns)

    expected_dto = TableModeDTO(
        table_id=my_uuid, table_name=table_name, table_type=update_table_type, table_columns=update_table_columns
    )
    assert updated_dto == expected_dto


def test_add_tablemode_failure_invalid_table_data():
    mock_tablemode_repo = Mock(spec=TablemodeRepository)
    tablemode_service = TableModeService(mock_tablemode_repo)
    my_uuid = uuid.uuid4()
    my_table_name = "test_name"

    # defining invalid and valid table_type / table_columns
    invalid_table_columns = [LinkColumn.ASSET_TYPE, ThermalColumn.EFFICIENCY]
    str_invalid_table_columns = ",".join(invalid_table_columns)

    my_table_type = TableType.AREA

    # mocking a tablemode that contains an invalid table_columns
    mock_tablemode_repo.save.return_value = TableMode(
        table_id=my_uuid,
        table_name=my_table_name,
        user_id=1,
        table_type=my_table_type,
        table_columns=str_invalid_table_columns,
    )
    with pytest.raises(
        HTTPException,
        match=f"422: Invalid columns {', '.join(invalid_table_columns)} for table type {my_table_type}",
    ):
        tablemode_service.add_table(my_table_name, my_table_type, invalid_table_columns)


def test_update_tablemode_failure_updating_non_existing_tablemode():
    # trying to update a tablemode that does not exist
    mock_tablemode_repo = Mock(spec=TablemodeRepository)
    my_uuid = uuid.uuid4()
    my_table_type = TableType.AREA
    my_table_columns = [AreaColumn.DISPATCHABLE_HYDRO_POWER, AreaColumn.NON_DISPATCHABLE_POWER]
    tablemode_service = TableModeService(mock_tablemode_repo)

    mock_tablemode_repo.get.return_value = None
    with pytest.raises(
        HTTPException,
        match=f"404: Tablemode with id {my_uuid} not found",
    ):
        tablemode_service.update_table(my_uuid, my_table_type, my_table_columns)


def test_update_tablemode_failure_updating_tablemode_with_invalid_table_data():
    mock_tablemode_repo = Mock(spec=TablemodeRepository)
    my_uuid = uuid.uuid4()
    my_table_name = "test_name"
    my_table_type = TableType.AREA
    incorrect_table_columns = [STStorageColumn.EFFICIENCY, STStorageColumn.ENABLED]
    incorrect_str_table_columns = ",".join(incorrect_table_columns)

    tablemode_service = TableModeService(mock_tablemode_repo)

    # trying to update the tablemode with an incorrect table_columns
    mock_tablemode_repo.get.return_value = TableMode(
        table_id=my_uuid,
        table_name=my_table_name,
        table_type=my_table_type,
        table_columns=incorrect_str_table_columns,
    )

    with pytest.raises(
        HTTPException,
        match=f"422: Invalid columns {', '.join(incorrect_table_columns)} for table type {my_table_type}",
    ):
        tablemode_service.update_table(my_uuid, my_table_type, incorrect_table_columns)


def test_delete_tablemode_failure_deleting_non_existing_tablemode():
    mock_tablemode_repo = Mock(spec=TablemodeRepository)

    my_uuid = uuid.uuid4()
    tablemode_service = TableModeService(mock_tablemode_repo)
    mock_tablemode_repo.get.return_value = None
    with pytest.raises(
        HTTPException,
        match=f"404: tablemode with id {my_uuid} not found",
    ):
        tablemode_service.delete_table(my_uuid)
