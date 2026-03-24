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

import json

from starlette.testclient import TestClient


def test_solver_presets(client: TestClient, user_access_token: str, admin_access_token: str) -> None:
    # Test creating solver presets
    payload1 = {
        "name": "test-xpress-config",
        "linear_solver": "xpress",
        "min_antares_version": "9.2",
        "linear_solver_param_optim_1": {"THREADS": "4", "PRESOLVE": "1"},
        "linear_solver_param_optim_2": {"MIPRELSTOP": "0.01"},
        "linear_solver_param": {"DEFAULTALG": "4"},
        "use_optim_1_basis_next_week": True,
        "use_optim_1_basis_optim_2": False,
    }

    res1 = client.post(
        "/v1/launcher/solver-presets",
        headers={"Authorization": f"Bearer {user_access_token}"},
        json=payload1,
    )

    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["name"] == "test-xpress-config"
    assert data1["linearSolver"] == "xpress"
    assert "id" in data1
    assert data1["minAntaresVersion"] == "9.2"
    assert data1["linearSolverParam"] == {"DEFAULTALG": "4"}
    assert data1["linearSolverParamOptim1"] == {"THREADS": "4", "PRESOLVE": "1"}
    assert data1["linearSolverParamOptim2"] == {"MIPRELSTOP": "0.01"}
    assert data1["useOptim1BasisOptim2"] is False

    # Test creating solver presets with minimal required fields
    payload2 = {
        "name": "minimal-config",
        "linear_solver": "sirius",
    }

    res2 = client.post(
        "/v1/launcher/solver-presets",
        headers={"Authorization": f"Bearer {user_access_token}"},
        json=payload2,
    )

    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["name"] == "minimal-config"
    assert data2["linearSolver"] == "sirius"
    assert data2["useOptim1BasisNextWeek"] is True
    assert data2["useOptim1BasisOptim2"] is True

    # Test retrieving a solver presets by ID
    # First create one
    create_payload3 = {
        "name": "retrieve-test",
        "linear_solver": "coin",
        "min_antares_version": "8.0",
        "linear_solver_param": {"THREADS": "2"},
    }

    create_res3 = client.post(
        "/v1/launcher/solver-presets",
        headers={"Authorization": f"Bearer {user_access_token}"},
        json=create_payload3,
    )
    config_id3 = create_res3.json()["id"]

    # Now retrieve it
    res3 = client.get(
        f"/v1/launcher/solver-presets/{config_id3}",
        headers={"Authorization": f"Bearer {user_access_token}"},
    )

    assert res3.status_code == 200
    data3 = res3.json()
    assert data3["id"] == config_id3
    assert data3["name"] == "retrieve-test"
    assert data3["linearSolver"] == "coin"
    assert data3["linearSolverParam"] == {"THREADS": "2"}

    # Test creating solver presets with empty name
    invalid_payload4 = {
        "name": "   ",  # Empty/whitespace name
        "linear_solver": "xpress",
    }

    res4 = client.post(
        "/v1/launcher/solver-presets",
        headers={"Authorization": f"Bearer {user_access_token}"},
        json=invalid_payload4,
    )

    assert res4.status_code == 422

    # Test creating solver presets with min > max version
    invalid_payload5 = {
        "name": "invalidversion",
        "linear_solver": "xpress",
        "min_antares_version": "9.2",
        "max_antares_version": "9.0",  # max < min
    }

    res5 = client.post(
        "/v1/launcher/solver-presets",
        headers={"Authorization": f"Bearer {user_access_token}"},
        json=invalid_payload5,
    )

    assert res5.status_code == 422

    # Test that optim params require min version >= 9.2
    invalid_payload6 = {
        "name": "invalid-optim-version",
        "linear_solver": "xpress",
        "min_antares_version": "8.0",  # < 9.2
        "linear_solver_param_optim_1": {"THREADS": "4"},  # Not allowed for < 9.2
    }

    res6 = client.post(
        "/v1/launcher/solver-presets",
        headers={"Authorization": f"Bearer {user_access_token}"},
        json=invalid_payload6,
    )

    assert res6.status_code == 422

    # Retrieve all configs created before
    res7 = client.get(
        "/v1/launcher/solver-presets/",
        headers={"Authorization": f"Bearer {user_access_token}"},
    )

    assert res7.status_code == 200
    data7 = res7.json()
    assert len(data7) == 3
    config_names7 = [c["name"] for c in data7]
    for expected_name_7 in ["test-xpress-config", "minimal-config", "retrieve-test"]:
        assert expected_name_7 in config_names7

    # Test updating solver presets
    update_payload8 = {
        "min_antares_version": "9.3",
    }

    # Get the ID of minimal-config
    config1_id = data1["id"]

    res8 = client.put(
        f"/v1/launcher/solver-presets/{config1_id}",
        headers={"Authorization": f"Bearer {admin_access_token}"},
        json=update_payload8,
    )

    assert res8.status_code == 200

    # Verify the update by retrieving the config again
    res8_verify = client.get(
        f"/v1/launcher/solver-presets/{config1_id}",
        headers={"Authorization": f"Bearer {admin_access_token}"},
    )

    assert res8_verify.status_code == 200
    data8_verify = res8_verify.json()
    assert data8_verify["minAntaresVersion"] == "9.3"
    assert data8_verify["linearSolver"] == "xpress"  # unchanged although not in update payload

    # Test that we can't update to version < 9.2 if optim params are defined
    update_payload9 = {
        "min_antares_version": "8.0",  # < 9.2
    }

    res9 = client.put(
        f"/v1/launcher/solver-presets/{config1_id}",  # config1 has optim_1 params defined
        headers={"Authorization": f"Bearer {admin_access_token}"},
        json=update_payload9,
    )

    assert res9.status_code == 422

    # Test running a study with a solver presets and verify launcher params
    get_studies_res = client.get(
        "/v1/studies",
        headers={"Authorization": f"Bearer {user_access_token}"},
    )
    studies = get_studies_res.json()
    study_id = next(id for id in studies if studies[id]["name"] == "STA-mini")

    res_run_with_conf = client.post(
        f"/v1/launcher/run/{study_id}",
        headers={"Authorization": f"Bearer {user_access_token}"},
        params={"solver_presets_id": data1["id"], "version": "9.3"},
    )

    job_id = res_run_with_conf.json()["job_id"]

    res = client.get(
        f"/v1/launcher/jobs?study_id={study_id}",
        headers={"Authorization": f"Bearer {user_access_token}"},
    )
    job_info = res.json()[0]
    assert job_info["id"] == job_id
    job_launcher_params_json = job_info["launcher_params"]
    job_launcher_params = json.loads(job_launcher_params_json)
    assert job_launcher_params["other_options"] == (
        'xpress nobasis2 param-optim1="DEFAULTALG 4 THREADS 4 PRESOLVE 1" param-optim2="DEFAULTALG 4 MIPRELSTOP 0.01"'
    )

    # Test updating optim params to None/empty when version < 9.2
    update_payload10 = {
        "min_antares_version": "8.0",  # < 9.2
        "linear_solver_param_optim_1": {},  # Override to empty
        "linear_solver_param_optim_2": {},  # Override to empty
    }

    res10 = client.put(
        f"/v1/launcher/solver-presets/{config1_id}",
        headers={"Authorization": f"Bearer {admin_access_token}"},
        json=update_payload10,
    )

    assert res10.status_code == 200

    # Verify the update
    res10_verify = client.get(
        f"/v1/launcher/solver-presets/{config1_id}",
        headers={"Authorization": f"Bearer {user_access_token}"},
    )

    assert res10_verify.status_code == 200
    data10_verify = res10_verify.json()
    assert data10_verify["minAntaresVersion"] == "8.0"
    assert data10_verify["linearSolverParamOptim1"] == {}
    assert data10_verify["linearSolverParamOptim2"] == {}

    # Test deleting solver presets
    res_delete = client.delete(
        f"/v1/launcher/solver-presets/{config1_id}",
        headers={"Authorization": f"Bearer {admin_access_token}"},
    )

    assert res_delete.status_code == 200

    # Verify it's deleted by trying to retrieve it
    res_deleted_verify = client.get(
        f"/v1/launcher/solver-presets/{config1_id}",
        headers={"Authorization": f"Bearer {admin_access_token}"},
    )

    assert res_deleted_verify.status_code == 404

    # Test that regular users cannot delete configurations (need admin)
    res_delete_user = client.delete(
        f"/v1/launcher/solver-presets/{config_id3}",
        headers={"Authorization": f"Bearer {user_access_token}"},
    )

    assert res_delete_user.status_code == 403

    # Test that regular users cannot update configurations (need admin)
    update_payload_user = {
        "min_antares_version": "8.0",
    }

    res_update_user = client.put(
        f"/v1/launcher/solver-presets/{config_id3}",
        headers={"Authorization": f"Bearer {user_access_token}"},
        json=update_payload_user,
    )

    assert res_update_user.status_code == 403
