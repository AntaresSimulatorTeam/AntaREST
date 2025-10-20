# Copyright (c) 2025, RTE (https://www.rte-france.com)
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

from starlette.testclient import TestClient


def test_launcher(client: TestClient, user_access_token: str) -> None:
    # Test creating a new launcher configuration
    payload1 = {
        "name": "test-xpress-config",
        "linear_solver": "xpress",
        "min_antares_version": {"major": 9, "minor": 2, "patch": 0},
        "linear_solver_param_optim_1": [["THREADS", "4"], ["PRESOLVE", "1"]],
        "linear_solver_param_optim_2": [["MIPRELSTOP", "0.01"]],
        "linear_solver_param": [["DEFAULTALG", "4"]],
        "use_optim_1_basis_next_week": True,
        "use_optim_1_basis_optim_2": False,
    }

    res1 = client.post(
        "/v1/launcher/configurations",
        headers={"Authorization": f"Bearer {user_access_token}"},
        json=payload1,
    )

    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["name"] == "test-xpress-config"
    assert data1["linear_solver"] == "xpress"
    assert "id" in data1
    assert data1["min_antares_version"] == {"major": 9, "minor": 2, "patch": 0}
    assert data1["linear_solver_param"] == [["DEFAULTALG", "4"]]
    assert data1["linear_solver_param_optim_1"] == [["THREADS", "4"], ["PRESOLVE", "1"]]
    assert data1["linear_solver_param_optim_2"] == [["MIPRELSTOP", "0.01"]]
    assert data1["use_optim_1_basis_optim_2"] is False

    # Test creating a launcher config with minimal required fields
    payload2 = {
        "name": "minimal-config",
        "linear_solver": "sirius",
    }

    res2 = client.post(
        "/v1/launcher/configurations",
        headers={"Authorization": f"Bearer {user_access_token}"},
        json=payload2,
    )

    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["name"] == "minimal-config"
    assert data2["linear_solver"] == "sirius"
    assert data2["use_optim_1_basis_next_week"] is True
    assert data2["use_optim_1_basis_optim_2"] is True

    # Test retrieving a launcher configuration by ID
    # First create a config
    create_payload3 = {
        "name": "retrieve-test",
        "linear_solver": "coin",
        "min_antares_version": {"major": 8, "minor": 0, "patch": 0},
        "linear_solver_param": [["THREADS", "2"]],
    }

    create_res3 = client.post(
        "/v1/launcher/configurations",
        headers={"Authorization": f"Bearer {user_access_token}"},
        json=create_payload3,
    )
    config_id3 = create_res3.json()["id"]

    # Now retrieve it
    res3 = client.get(
        f"/v1/launcher/configurations/{config_id3}",
        headers={"Authorization": f"Bearer {user_access_token}"},
    )

    assert res3.status_code == 200
    data3 = res3.json()
    assert data3["id"] == config_id3
    assert data3["name"] == "retrieve-test"
    assert data3["linear_solver"] == "coin"
    assert data3["linear_solver_param"] == [["THREADS", "2"]]

    # Test creating a launcher config with empty name
    invalid_payload4 = {
        "name": "   ",  # Empty/whitespace name
        "linear_solver": "xpress",
    }

    res4 = client.post(
        "/v1/launcher/configurations",
        headers={"Authorization": f"Bearer {user_access_token}"},
        json=invalid_payload4,
    )

    assert res4.status_code == 422

    # Test creating a launcher config with min > max version
    invalid_payload5 = {
        "name": "invalidversion",
        "linear_solver": "xpress",
        "min_antares_version": {"major": 9, "minor": 2, "patch": 0},
        "max_antares_version": {"major": 9, "minor": 0, "patch": 0},  # max < min
    }

    res5 = client.post(
        "/v1/launcher/configurations",
        headers={"Authorization": f"Bearer {user_access_token}"},
        json=invalid_payload5,
    )

    assert res5.status_code == 422

    # Test that optim params require min version >= 9.2
    invalid_payload6 = {
        "name": "invalid-optim-version",
        "linear_solver": "xpress",
        "min_antares_version": "8.0.0",  # < 9.2
        "linear_solver_param_optim_1": [["THREADS", "4"]],  # Not allowed for < 9.2
    }

    res6 = client.post(
        "/v1/launcher/configurations",
        headers={"Authorization": f"Bearer {user_access_token}"},
        json=invalid_payload6,
    )

    assert res6.status_code == 422

    # Retrieve all configs created before
    res7 = client.get(
        "/v1/launcher/configurations/",
        headers={"Authorization": f"Bearer {user_access_token}"},
    )

    assert res7.status_code == 200
    data7 = res7.json()
    assert len(data7) == 3
    config_names7 = [c["name"] for c in data7]
    for expected_name_7 in ["test-xpress-config", "minimal-config", "retrieve-test"]:
        assert expected_name_7 in config_names7
