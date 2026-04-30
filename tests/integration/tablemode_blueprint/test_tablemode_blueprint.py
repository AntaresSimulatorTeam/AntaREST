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

from antarest.tablemode.model import AreaColumn, STStorageColumn, TableType


def test_tablemode_success(client: TestClient, admin_access_token: str) -> None:
    client.headers = {"Authorization": f"Bearer {admin_access_token}"}

    # success : creating a tablemode
    res_post = client.post(
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
    res_put = client.put(
        f"/v1/tablemode/{str(table_id)}",
        json={"table_type": TableType.AREA, "table_columns": [AreaColumn.DISPATCHABLE_HYDRO_POWER]},
    )
    assert res_put.status_code == 200
    assert res_put.json()["table_id"] == table_id
    assert res_put.json()["table_name"] == "my_table"
    assert res_put.json()["table_type"] == TableType.AREA
    assert res_put.json()["table_columns"] == [AreaColumn.DISPATCHABLE_HYDRO_POWER]

    # success : updating a tablemode's table_columns
    res_put = client.put(
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
    res_delete = client.delete(f"/v1/tablemode/{str(table_id)}")
    assert res_delete.status_code == 200


def test_tablemode_fail(client: TestClient, admin_access_token: str) -> None:
    client.headers = {"Authorization": f"Bearer {admin_access_token}"}
    # non_existing_table_id = "non-existing-id"
    my_uuid = uuid.uuid4()
    # fail : trying to delete a non-existing tablemode
    res_del_fail = client.delete(f"/v1/tablemode/{str(my_uuid)}")
    assert res_del_fail.status_code == 404

    # trying to update a non-existing tablemode
    res_update_fail = client.put(
        f"/v1/tablemode/{str(my_uuid)}",
        json={
            "table_type": TableType.ST_STORAGE,
            "table_columns": [STStorageColumn.ENABLED, STStorageColumn.EFFICIENCY],
        },
    )
    assert res_update_fail.status_code == 404

    # creating a tablemode with non existing datas (table_type and table_columns)
    res_post_non_existing_name = client.post(
        "/v1/tablemode", json={"table_name": "", "table_type": TableType.AREA, "table_columns": ["non_existing_power"]}
    )
    assert res_post_non_existing_name.status_code == 422
    assert res_post_non_existing_name.json()["description"] == "String should have at least 1 character"

    res_post_non_existing_type = client.post(
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

    res_post_non_existing_columns = client.post(
        "/v1/tablemode",
        json={"table_name": "my_table", "table_type": TableType.AREA, "table_columns": ["non_existing_power"]},
    )
    assert res_post_non_existing_columns.status_code == 422
    assert res_post_non_existing_columns.json()["description"] == (
        "Input should be 'nonDispatchPower', 'dispatchHydroPower', 'otherDispatchPower', 'energyCostUnsupplied', 'spreadUnsuppliedEnergyCost', 'energyCostSpilled', 'spreadSpilledEnergyCost', 'filterSynthesis', 'filterByYear' or 'adequacyPatchMode'"
    )

    res_update_existing_tablemode_but_non_existing_table_type = client.put(
        f"/v1/tablemode/{str(my_uuid)}",
        json={"table_type": "non_existing_type", "table_columns": [AreaColumn.DISPATCHABLE_HYDRO_POWER]},
    )
    assert res_update_existing_tablemode_but_non_existing_table_type.status_code == 422
    assert res_update_existing_tablemode_but_non_existing_table_type.json()["description"] == (
        "Input should be 'areas', 'links', 'thermals', 'renewables', 'st-storages', 'binding-constraints' or 'st-storages-additional-constraints'"
    )

    res_update_existing_tablemode_but_non_existing_table_columns = client.put(
        f"/v1/tablemode/{str(my_uuid)}", json={"table_type": TableType.AREA, "table_columns": ["non_existing_power"]}
    )
    assert res_update_existing_tablemode_but_non_existing_table_columns.status_code == 422
    assert res_update_existing_tablemode_but_non_existing_table_columns.json()["description"] == (
        "Input should be 'nonDispatchPower', 'dispatchHydroPower', 'otherDispatchPower', 'energyCostUnsupplied', 'spreadUnsuppliedEnergyCost', 'energyCostSpilled', 'spreadSpilledEnergyCost', 'filterSynthesis', 'filterByYear' or 'adequacyPatchMode'"
    )
