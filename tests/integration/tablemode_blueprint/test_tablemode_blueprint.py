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

from starlette.testclient import TestClient

from antarest.tablemode.model import (
    AreaColumn,
    BindingConstraintColumn,
    LinkColumn,
    RenewableColumn,
    STStorageAdditionalConstraintsColumn,
    STStorageColumn,
    TableType,
    ThermalColumn,
)


def test_tablemode_success(admin_client: TestClient, admin_access_token: str) -> None:
    # success : creating a tablemode
    res_post = admin_client.post(
        "/v1/tablemode",
        json={
            "table_name": "my_table",
            "table_type": TableType.AREA,
            "table_columns": [AreaColumn.DISPATCHABLE_HYDRO_POWER],
        },
    )
    json_post = res_post.json()
    table_id = json_post["table_id"]

    assert res_post.status_code == 201
    assert json_post["table_name"] == "my_table"
    assert json_post["table_type"] == TableType.AREA
    assert json_post["table_columns"] == [AreaColumn.DISPATCHABLE_HYDRO_POWER]

    # success : updating a tablemode's table_type
    res_put = admin_client.put(
        f"/v1/tablemode/{str(table_id)}",
        json={
            "table_type": TableType.ST_STORAGE_ADDITIONAL_CONSTRAINTS,
            "table_columns": [
                STStorageAdditionalConstraintsColumn.ENABLED,
                STStorageAdditionalConstraintsColumn.VARIABLE,
            ],
        },
    )
    assert res_put.status_code == 200
    assert res_put.json()["table_id"] == table_id
    assert res_put.json()["table_name"] == "my_table"
    assert res_put.json()["table_type"] == TableType.ST_STORAGE_ADDITIONAL_CONSTRAINTS
    assert res_put.json()["table_columns"] == [
        STStorageAdditionalConstraintsColumn.ENABLED,
        STStorageAdditionalConstraintsColumn.VARIABLE,
    ]

    # success : updating a tablemode's table_columns
    res_put = admin_client.put(
        f"/v1/tablemode/{str(table_id)}",
        json={
            "table_type": TableType.AREA,
            "table_columns": [AreaColumn.NON_DISPATCHABLE_POWER, AreaColumn.DISPATCHABLE_HYDRO_POWER],
        },
    )
    assert res_put.status_code == 200
    assert res_put.json()["table_id"] == table_id
    assert res_put.json()["table_name"] == "my_table"
    assert res_put.json()["table_type"] == TableType.AREA
    assert res_put.json()["table_columns"] == [AreaColumn.NON_DISPATCHABLE_POWER, AreaColumn.DISPATCHABLE_HYDRO_POWER]

    # success : deleting a tablemode and checking it doesn't exist anymore
    res_delete = admin_client.delete(f"/v1/tablemode/{str(table_id)}")
    assert res_delete.status_code == 200

    res_get_after_delete = admin_client.get("/v1/tablemode")
    assert res_get_after_delete.status_code == 200
    json_get_after_delete = res_get_after_delete.json()
    assert json_get_after_delete == []


def test_tablemode_fail(admin_client: TestClient, admin_access_token: str) -> None:
    # non_existing_table_id = "non-existing-id"
    my_uuid = uuid.uuid4()
    # fail : trying to delete a non-existing tablemode
    res_del_fail = admin_client.delete(f"/v1/tablemode/{str(my_uuid)}")
    assert res_del_fail.status_code == 404

    # trying to update a non-existing tablemode
    res_update_fail = admin_client.put(
        f"/v1/tablemode/{str(my_uuid)}",
        json={
            "table_type": TableType.ST_STORAGE,
            "table_columns": [STStorageColumn.ENABLED, STStorageColumn.EFFICIENCY],
        },
    )
    assert res_update_fail.status_code == 404

    # creating a tablemode with non existing datas (table_type and table_columns)
    res_post_non_existing_name = admin_client.post(
        "/v1/tablemode", json={"table_name": "", "table_type": TableType.AREA, "table_columns": ["non_existing_power"]}
    )
    assert res_post_non_existing_name.status_code == 422
    assert res_post_non_existing_name.json()["description"] == "String should have at least 1 character"

    res_post_non_existing_type = admin_client.post(
        "/v1/tablemode",
        json={
            "table_name": "my_table",
            "table_type": "non_existing_type",
            "table_columns": [AreaColumn.DISPATCHABLE_HYDRO_POWER],
        },
    )
    assert res_post_non_existing_type.status_code == 422
    assert res_post_non_existing_type.json()["description"] == (
        "Input should be 'areas', 'links', 'thermals', 'renewables', 'st-storages', 'binding-constraints' or 'st-storages-additional-constraints'"
    )

    res_post_non_existing_columns = admin_client.post(
        "/v1/tablemode",
        json={"table_name": "my_table", "table_type": TableType.AREA, "table_columns": ["non_existing_power"]},
    )
    assert res_post_non_existing_columns.status_code == 422
    assert res_post_non_existing_columns.json()["description"] == (
        "Input should be 'nonDispatchPower', 'dispatchHydroPower', 'otherDispatchPower', 'energyCostUnsupplied', 'spreadUnsuppliedEnergyCost', 'energyCostSpilled', 'spreadSpilledEnergyCost', 'filterSynthesis', 'filterByYear' or 'adequacyPatchMode'"
    )

    res_update_existing_tablemode_but_non_existing_table_type = admin_client.put(
        f"/v1/tablemode/{str(my_uuid)}",
        json={"table_type": "non_existing_type", "table_columns": [AreaColumn.DISPATCHABLE_HYDRO_POWER]},
    )
    assert res_update_existing_tablemode_but_non_existing_table_type.status_code == 422
    assert res_update_existing_tablemode_but_non_existing_table_type.json()["description"] == (
        "Input should be 'areas', 'links', 'thermals', 'renewables', 'st-storages', 'binding-constraints' or 'st-storages-additional-constraints'"
    )

    res_update_existing_tablemode_but_non_existing_table_columns = admin_client.put(
        f"/v1/tablemode/{str(my_uuid)}", json={"table_type": TableType.AREA, "table_columns": ["non_existing_power"]}
    )
    assert res_update_existing_tablemode_but_non_existing_table_columns.status_code == 422
    assert res_update_existing_tablemode_but_non_existing_table_columns.json()["description"] == (
        "Input should be 'nonDispatchPower', 'dispatchHydroPower', 'otherDispatchPower', 'energyCostUnsupplied', 'spreadUnsuppliedEnergyCost', 'energyCostSpilled', 'spreadSpilledEnergyCost', 'filterSynthesis', 'filterByYear' or 'adequacyPatchMode'"
    )


def test_tablemode_area_type_success(admin_client: TestClient, admin_access_token: str):
    """Test creating a table with valid AREA columns"""
    table_data = {
        "table_name": "Valid Area Table",
        "table_type": TableType.AREA,
        "table_columns": [AreaColumn.NON_DISPATCHABLE_POWER, AreaColumn.FILTER_SYNTHESIS],
    }
    response = admin_client.post("/v1/tablemode", json=table_data)
    assert response.status_code == 201
    result = response.json()
    assert result["table_name"] == "Valid Area Table"
    assert result["table_type"] == TableType.AREA


def test_tablemode_area_type_failure(admin_client: TestClient, admin_access_token: str):
    """Test creating a table with invalid AREA columns"""
    table_data = {
        "table_name": "Invalid Area Table",
        "table_type": TableType.AREA,
        "table_columns": [ThermalColumn.EFFICIENCY, LinkColumn.HURDLES_COST],
    }
    str_columns = ", ".join(table_data["table_columns"])
    response = admin_client.post("/v1/tablemode", json=table_data)
    assert response.status_code == 422
    assert response.json()["description"] == f"Invalid columns {str_columns} for table type areas"


# LINK table type tests
def test_tablemode_link_type_success(admin_client: TestClient, admin_access_token: str):
    """Test creating a table with valid LINK columns"""
    table_data = {
        "table_name": "Valid Link Table",
        "table_type": TableType.LINK,
        "table_columns": [LinkColumn.ASSET_TYPE, LinkColumn.COMMENTS, LinkColumn.HURDLES_COST],
    }
    response = admin_client.post("/v1/tablemode", json=table_data)
    assert response.status_code == 201
    result = response.json()
    assert result["table_name"] == "Valid Link Table"
    assert result["table_type"] == TableType.LINK


def test_tablemode_link_type_failure(admin_client: TestClient, admin_access_token: str):
    """Test creating a table with invalid LINK columns"""
    table_data = {
        "table_name": "Invalid Link Table",
        "table_type": TableType.LINK,
        "table_columns": [ThermalColumn.GROUP, AreaColumn.FILTER_SYNTHESIS],
    }
    response = admin_client.post("/v1/tablemode", json=table_data)
    assert response.status_code == 422
    # filterSynthesis isn't mentioned in the error message as it is also a column of the LINK columns table
    assert response.json()["description"] == "Invalid columns group for table type links"


# THERMAL table type tests
def test_tablemode_thermal_type_success(admin_client: TestClient, admin_access_token: str):
    """Test creating a table with valid THERMAL columns"""
    table_data = {
        "table_name": "Valid Thermal Table",
        "table_type": TableType.THERMAL,
        "table_columns": [ThermalColumn.GROUP, ThermalColumn.ENABLED, ThermalColumn.EFFICIENCY],
    }
    response = admin_client.post("/v1/tablemode", json=table_data)
    assert response.status_code == 201
    result = response.json()
    assert result["table_name"] == "Valid Thermal Table"
    assert result["table_type"] == TableType.THERMAL


def test_tablemode_thermal_type_failure(admin_client: TestClient, admin_access_token: str):
    """Test creating a table with invalid THERMAL columns"""
    table_data = {
        "table_name": "Invalid Thermal Table",
        "table_type": TableType.THERMAL,
        "table_columns": [LinkColumn.LOOP_FLOW, RenewableColumn.TS_INTERPRETATION],
    }
    str_columns = ", ".join(table_data["table_columns"])
    response = admin_client.post("/v1/tablemode", json=table_data)
    assert response.status_code == 422
    assert response.json()["description"] == f"Invalid columns {str_columns} for table type thermals"


# RENEWABLE table type tests
def test_tablemode_renewable_type_success(admin_client: TestClient, admin_access_token: str):
    """Test creating a table with valid RENEWABLE columns"""
    table_data = {
        "table_name": "Valid Renewable Table",
        "table_type": TableType.RENEWABLE,
        "table_columns": [RenewableColumn.ENABLED, RenewableColumn.GROUP, RenewableColumn.UNIT_COUNT],
    }
    response = admin_client.post("/v1/tablemode", json=table_data)
    assert response.status_code == 201
    result = response.json()
    assert result["table_name"] == "Valid Renewable Table"
    assert result["table_type"] == TableType.RENEWABLE


def test_tablemode_renewable_type_failure(admin_client: TestClient, admin_access_token: str):
    """Test creating a table with invalid RENEWABLE columns"""
    table_data = {
        "table_name": "Invalid Renewable Table",
        "table_type": TableType.RENEWABLE,
        "table_columns": [STStorageColumn.EFFICIENCY, ThermalColumn.MARGINAL_COST],
    }
    str_columns = ", ".join(table_data["table_columns"])
    response = admin_client.post("/v1/tablemode", json=table_data)
    assert response.status_code == 422
    assert response.json()["description"] == f"Invalid columns {str_columns} for table type renewables"


# ST_STORAGE table type tests
def test_tablemode_st_storage_type_success(admin_client: TestClient, admin_access_token: str):
    """Test creating a table with valid ST_STORAGE columns"""
    table_data = {
        "table_name": "Valid ST Storage Table",
        "table_type": TableType.ST_STORAGE,
        "table_columns": [STStorageColumn.GROUP, STStorageColumn.EFFICIENCY, STStorageColumn.INITIAL_LEVEL],
    }
    response = admin_client.post("/v1/tablemode", json=table_data)
    assert response.status_code == 201
    result = response.json()
    assert result["table_name"] == "Valid ST Storage Table"
    assert result["table_type"] == TableType.ST_STORAGE
    assert result["table_columns"] == [STStorageColumn.GROUP, STStorageColumn.EFFICIENCY, STStorageColumn.INITIAL_LEVEL]


def test_tablemode_st_storage_type_failure(admin_client: TestClient, admin_access_token: str):
    """Test creating a table with invalid ST_STORAGE columns"""
    table_data = {
        "table_name": "Invalid ST Storage Table",
        "table_type": TableType.ST_STORAGE,
        "table_columns": [AreaColumn.ENERGY_COST_UNSUPPLIED, BindingConstraintColumn.OPERATOR],
    }
    str_columns = ", ".join(table_data["table_columns"])
    response = admin_client.post("/v1/tablemode", json=table_data)
    assert response.status_code == 422
    assert response.json()["description"] == f"Invalid columns {str_columns} for table type st-storages"


# BINDING_CONSTRAINT table type tests
def test_tablemode_binding_constraint_type_success(admin_client: TestClient, admin_access_token: str):
    """Test creating a table with valid BINDING_CONSTRAINT columns"""
    table_data = {
        "table_name": "Valid Binding Constraint Table",
        "table_type": TableType.BINDING_CONSTRAINT,
        "table_columns": [
            BindingConstraintColumn.ENABLED,
            BindingConstraintColumn.TIME_STEP,
            BindingConstraintColumn.OPERATOR,
        ],
    }
    response = admin_client.post("/v1/tablemode", json=table_data)
    assert response.status_code == 201
    result = response.json()
    assert result["table_name"] == "Valid Binding Constraint Table"
    assert result["table_type"] == TableType.BINDING_CONSTRAINT


def test_tablemode_binding_constraint_type_failure(admin_client: TestClient, admin_access_token: str):
    """Test creating a table with invalid BINDING_CONSTRAINT columns"""
    table_data = {
        "table_name": "Invalid Binding Constraint Table",
        "table_type": TableType.BINDING_CONSTRAINT,
        "table_columns": [LinkColumn.LINK_WIDTH, RenewableColumn.NOMINAL_CAPACITY],
    }
    str_columns = ", ".join(table_data["table_columns"])
    response = admin_client.post("/v1/tablemode", json=table_data)
    assert response.status_code == 422
    assert response.json()["description"] == f"Invalid columns {str_columns} for table type binding-constraints"


# ST_STORAGE_ADDITIONAL_CONSTRAINTS table type tests
def test_tablemode_st_storage_additional_constraints_type_success(admin_client: TestClient, admin_access_token: str):
    """Test creating a table with valid ST_STORAGE_ADDITIONAL_CONSTRAINTS columns"""
    table_data = {
        "table_name": "Valid ST Storage Additional Constraints Table",
        "table_type": TableType.ST_STORAGE_ADDITIONAL_CONSTRAINTS,
        "table_columns": [
            STStorageAdditionalConstraintsColumn.VARIABLE,
            STStorageAdditionalConstraintsColumn.OPERATOR,
            STStorageAdditionalConstraintsColumn.ENABLED,
        ],
    }
    response = admin_client.post("/v1/tablemode", json=table_data)
    assert response.status_code == 201
    result = response.json()
    assert result["table_name"] == "Valid ST Storage Additional Constraints Table"
    assert result["table_type"] == TableType.ST_STORAGE_ADDITIONAL_CONSTRAINTS


def test_tablemode_st_storage_additional_constraints_type_failure(admin_client: TestClient, admin_access_token: str):
    """Test creating a table with invalid ST_STORAGE_ADDITIONAL_CONSTRAINTS columns"""
    table_data = {
        "table_name": "Invalid ST Storage Additional Constraints Table",
        "table_type": TableType.ST_STORAGE_ADDITIONAL_CONSTRAINTS,
        "table_columns": [AreaColumn.ADEQUACY_PATCH_MODE, ThermalColumn.CO2],
    }
    str_columns = ", ".join(table_data["table_columns"])
    response = admin_client.post("/v1/tablemode", json=table_data)
    assert response.status_code == 422
    assert (
        response.json()["description"]
        == f"Invalid columns {str_columns} for table type st-storages-additional-constraints"
    )
