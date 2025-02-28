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

import io
import re
import typing as t
from pathlib import Path
from unittest.mock import ANY
from urllib.parse import urljoin

import pytest
from starlette.testclient import TestClient

from antarest.core.tasks.model import TaskStatus
from antarest.study.business.xpansion_management import XpansionCandidateDTO
from tests.integration.utils import wait_task_completion


def _create_area(
    client: TestClient,
    study_id: str,
    area_name: str,
    *,
    country: str,
) -> str:
    res = client.post(
        f"/v1/studies/{study_id}/areas",
        json={"name": area_name, "type": "AREA", "metadata": {"country": country}},
    )
    assert res.status_code in {200, 201}, res.json()
    return t.cast(str, res.json()["id"])


def _create_link(
    client: TestClient,
    study_id: str,
    src_area_id: str,
    dst_area_id: str,
) -> None:
    res = client.post(f"/v1/studies/{study_id}/links", json={"area1": src_area_id, "area2": dst_area_id})
    assert res.status_code in {200, 201}, res.json()


def test_xpansion_with_upgrade(client: TestClient, tmp_path: Path, user_access_token: str) -> None:
    headers = {"Authorization": f"Bearer {user_access_token}"}
    client.headers = headers

    # Create a Study in version 860
    res = client.post("/v1/studies", params={"name": "foo", "version": "860"})
    assert res.status_code == 201, res.json()
    study_id = res.json()

    # Create a xpansion configuration
    res = client.post(f"/v1/studies/{study_id}/extensions/xpansion")
    assert res.status_code in {200, 201}, res.json()

    # Create a capacity matrix
    raw_url = f"/v1/studies/{study_id}/raw"
    matrix_name = "matrix_test"
    matrix_path = f"user/expansion/capa/{matrix_name}"
    content = b"1.20000\n3.400000\n"
    res = client.post(
        f"/v1/studies/{study_id}/extensions/xpansion/resources/capacities",
        files={"file": (matrix_name, io.BytesIO(content))},
    )
    assert res.status_code == 200, res.json()
    res = client.get(raw_url, params={"path": matrix_path})
    written_data = res.json()["data"]
    assert written_data == [[1.2], [3.4]]
    file_path = tmp_path / "internal_workspace" / study_id / "user" / "expansion" / "capa" / f"{matrix_name}.link"
    assert file_path.exists()

    # Upgrades it to version 870 or higher (this will trigger the normalization of the capacity matrix)
    res = client.put(f"/v1/studies/{study_id}/upgrade")
    assert res.status_code == 200
    task_id = res.json()
    task = wait_task_completion(client, user_access_token, task_id)
    assert task.status == TaskStatus.COMPLETED

    # Checks that we can still access the capacity file even if it was normalized
    file_path = tmp_path / "internal_workspace" / study_id / "user" / "expansion" / "capa" / f"{matrix_name}.link"
    assert file_path.exists()
    res = client.get(raw_url, params={"path": matrix_path})
    written_data = res.json()["data"]
    assert written_data == [[1.2], [3.4]]


@pytest.mark.parametrize("study_type", ["raw", "variant"])
def test_integration_xpansion(client: TestClient, tmp_path: Path, admin_access_token: str, study_type: str) -> None:
    headers = {"Authorization": f"Bearer {admin_access_token}"}
    client.headers = headers

    res = client.post("/v1/studies", params={"name": "foo", "version": "860"})
    assert res.status_code == 201, res.json()
    study_id = res.json()

    area1_id = _create_area(client, study_id, "area1", country="FR")
    area2_id = _create_area(client, study_id, "area2", country="DE")
    area3_id = _create_area(client, study_id, "area3", country="DE")
    _create_link(client, study_id, area1_id, area2_id)

    if study_type == "variant":
        res = client.post(f"/v1/studies/{study_id}/variants", params={"name": "variant 1"})
        study_id = res.json()

    res = client.post(f"/v1/studies/{study_id}/extensions/xpansion")
    assert res.status_code in {200, 201}, res.json()

    expansion_path = tmp_path / "internal_workspace" / study_id / "user" / "expansion"
    if study_type == "variant":
        expansion_path = tmp_path / "internal_workspace" / study_id / "snapshot" / "user" / "expansion"

    # Create a client for Xpansion with the xpansion URL
    xpansion_base_url = f"/v1/studies/{study_id}/extensions/xpansion/"
    xp_client = TestClient(client.app, base_url=urljoin(str(client.base_url), xpansion_base_url))
    xp_client.headers = headers
    res = xp_client.get("settings")
    assert res.status_code == 200
    assert res.json() == {
        "master": "integer",
        "uc_type": "expansion_fast",
        "optimality_gap": 1.0,
        "relative_gap": 1e-06,
        "relaxed_optimality_gap": 1e-05,
        "max_iteration": 1000,
        "solver": "Xpress",
        "log_level": 0,
        "separation_parameter": 0.5,
        "batch_size": 96,
        "yearly-weights": "",
        "additional-constraints": "",
        "timelimit": 1000000000000,
        "sensitivity_config": {"epsilon": 0.0, "projection": [], "capex": False},
    }

    res = xp_client.put("settings", json={"optimality_gap": 42})
    assert res.status_code == 200
    assert res.json() == {
        "master": "integer",
        "uc_type": "expansion_fast",
        "optimality_gap": 42,
        "relative_gap": 1e-06,
        "relaxed_optimality_gap": 1e-05,
        "max_iteration": 1000,
        "solver": "Xpress",
        "log_level": 0,
        "separation_parameter": 0.5,
        "batch_size": 96,
        "yearly-weights": "",
        "additional-constraints": "",
        "timelimit": 1000000000000,
        "sensitivity_config": {"epsilon": 0.0, "projection": [], "capex": False},
    }

    res = xp_client.put("settings", json={"additional-constraints": "missing.txt"})
    assert res.status_code == 404
    err_obj = res.json()
    assert re.search(r"file 'missing.txt' does not exist", err_obj["description"])
    assert err_obj["exception"] == "XpansionFileNotFoundError"

    res = xp_client.put("settings/additional-constraints", params={"filename": "missing.txt"})
    assert res.status_code == 404
    err_obj = res.json()
    assert re.search(r"file 'missing.txt' does not exist", err_obj["description"])
    assert err_obj["exception"] == "XpansionFileNotFoundError"

    filename_constraints1 = "filename_constraints1.txt"
    filename_constraints2 = "filename_constraints2.txt"
    filename_constraints3 = "filename_constraints3.txt"
    content_constraints1 = "content_constraints1\n"
    content_constraints2 = "content_constraints2\n"
    content_constraints3 = "content_constraints3\n"

    files = {
        "file": (
            filename_constraints1,
            io.BytesIO(content_constraints1.encode("utf-8")),
            "image/jpeg",
        )
    }
    res = xp_client.post("resources/constraints", files=files)
    assert res.status_code in {200, 201}
    actual_path = expansion_path / "constraints" / filename_constraints1
    if study_type == "variant":
        # Generate the fs to check the content
        task_id = client.put(f"/v1/studies/{study_id}/generate").json()
        res = client.get(f"/v1/tasks/{task_id}?wait_for_completion=True")
        assert res.status_code == 200
    assert actual_path.read_text() == content_constraints1

    files = {
        "file": (
            filename_constraints1,
            io.BytesIO(content_constraints1.encode("utf-8")),
            "image/jpeg",
        ),
    }

    res = xp_client.post("resources/constraints", files=files)
    assert res.status_code == 409
    err_obj = res.json()
    assert re.search(
        rf"File '{filename_constraints1}' already exists",
        err_obj["description"],
        flags=re.IGNORECASE,
    )
    assert err_obj["exception"] == "XpansionFileAlreadyExistsError"

    files = {
        "file": (
            filename_constraints2,
            io.BytesIO(content_constraints2.encode("utf-8")),
            "image/jpeg",
        ),
    }
    res = xp_client.post("resources/constraints", files=files)
    assert res.status_code in {200, 201}

    files = {
        "file": (
            filename_constraints3,
            io.BytesIO(content_constraints3.encode("utf-8")),
            "image/jpeg",
        ),
    }
    res = xp_client.post("resources/constraints", files=files)
    assert res.status_code in {200, 201}

    res = xp_client.get(f"resources/constraints/{filename_constraints1}")
    assert res.status_code == 200
    assert res.json() == content_constraints1

    res = xp_client.get("resources/constraints/")
    assert res.status_code == 200
    assert res.json() == [
        filename_constraints1,
        filename_constraints2,
        filename_constraints3,
    ]

    res = xp_client.put("settings/additional-constraints", params={"filename": filename_constraints1})
    assert res.status_code == 200

    res = xp_client.delete(f"resources/constraints/{filename_constraints1}")
    assert res.status_code == 409
    err_obj = res.json()
    assert re.search(
        rf"File '{filename_constraints1}' is still used",
        err_obj["description"],
        flags=re.IGNORECASE,
    )
    assert err_obj["exception"] == "FileCurrentlyUsedInSettings"

    res = xp_client.put("settings/additional-constraints")
    assert res.status_code == 200

    res = xp_client.delete(f"resources/constraints/{filename_constraints1}")
    assert res.status_code == 200

    candidate1 = {
        "name": "candidate1",
        "link": f"{area1_id} - {area2_id}",
        "annual-cost-per-mw": 1,
        "max-investment": 1.0,
    }
    res = xp_client.post("candidates", json=candidate1)
    assert res.status_code in {200, 201}

    candidate2 = {
        "name": "candidate2",
        "link": f"{area1_id} - {area3_id}",
        "annual-cost-per-mw": 1,
        "max-investment": 1.0,
    }
    res = xp_client.post("candidates", json=candidate2)
    assert res.status_code == 404
    err_obj = res.json()
    assert re.search(
        rf"link from '{area1_id}' to '{area3_id}' not found",
        err_obj["description"],
        flags=re.IGNORECASE,
    )
    assert err_obj["exception"] == "LinkNotFound"

    candidate3 = {
        "name": "candidate3",
        "link": f"non_existent_area - {area3_id}",
        "annual-cost-per-mw": 1,
        "max-investment": 1.0,
    }
    res = xp_client.post("candidates", json=candidate3)
    assert res.status_code == 404
    err_obj = res.json()
    assert re.search(
        rf"link from '{area3_id}' to 'non_existent_area' not found",
        err_obj["description"],
        flags=re.IGNORECASE,
    )
    assert err_obj["exception"] == "LinkNotFound"

    # Creates a capacity file
    filename_capa1 = "filename_capa1.txt"
    content_capa1 = "0"
    files = {
        "file": (
            filename_capa1,
            io.BytesIO(content_capa1.encode("utf-8")),
            "txt/csv",
        )
    }
    res = xp_client.post("resources/capacities", files=files)
    assert res.status_code in {200, 201}
    actual_path = expansion_path / "capa" / f"{filename_capa1}.link"
    if study_type == "variant":
        # Generate the fs to check the content
        task_id = client.put(f"/v1/studies/{study_id}/generate").json()
        res = client.get(f"/v1/tasks/{task_id}?wait_for_completion=True")
        assert res.status_code == 200
    assert actual_path.exists()

    # Creates another one
    filename_capa2 = "filename_capa2.txt"
    content_capa2 = "1"
    res = xp_client.post("resources/capacities", files=files)
    assert res.status_code == 409
    err_obj = res.json()
    assert re.search(
        rf"File '{filename_capa1}' already exists",
        err_obj["description"],
        flags=re.IGNORECASE,
    )
    assert err_obj["exception"] == "XpansionFileAlreadyExistsError"

    files = {
        "file": (
            filename_capa2,
            io.BytesIO(content_capa2.encode("utf-8")),
            "txt/csv",
        )
    }
    res = xp_client.post("resources/capacities", files=files)
    assert res.status_code in {200, 201}

    # Creates a 3rd one
    filename_capa3 = "filename_capa3.txt"
    content_capa3 = "2"
    files = {
        "file": (
            filename_capa3,
            io.BytesIO(content_capa3.encode("utf-8")),
            "txt/csv",
        )
    }
    res = xp_client.post("resources/capacities", files=files)
    assert res.status_code in {200, 201}

    # get single capa
    res = xp_client.get(f"resources/capacities/{filename_capa1}")
    assert res.status_code == 200
    assert res.json() == {
        "columns": [0],
        "data": [[0.0]],
        "index": [0],
    }

    res = xp_client.get("resources/capacities")
    assert res.status_code == 200
    assert res.json() == [filename_capa1, filename_capa2, filename_capa3]

    candidate4 = {
        "name": "candidate4",
        "link": f"{area1_id} - {area2_id}",
        "annual-cost-per-mw": 1,
        "max-investment": 1.0,
        "link-profile": filename_capa1,
    }
    res = xp_client.post("candidates", json=candidate4)
    assert res.status_code in {200, 201}

    res = xp_client.get(f"candidates/{candidate1['name']}")
    assert res.status_code == 200
    assert res.json() == XpansionCandidateDTO.model_validate(candidate1).model_dump(by_alias=True)

    res = xp_client.get("candidates")
    assert res.status_code == 200
    assert res.json() == [
        XpansionCandidateDTO.model_validate(candidate1).model_dump(by_alias=True),
        XpansionCandidateDTO.model_validate(candidate4).model_dump(by_alias=True),
    ]

    res = xp_client.delete(f"resources/capacities/{filename_capa1}")
    assert res.status_code == 409
    err_obj = res.json()
    assert re.search(
        rf"capacities file '{filename_capa1}' is still used",
        err_obj["description"],
        flags=re.IGNORECASE,
    )

    candidate5 = {
        "name": "candidate4",
        "link": f"{area1_id} - {area2_id}",
        "annual-cost-per-mw": 1,
        "max-investment": 1.0,
    }
    res = xp_client.put(f"candidates/{candidate4['name']}", json=candidate5)
    assert res.status_code == 200

    res = xp_client.delete(f"resources/capacities/{filename_capa1}")
    assert res.status_code == 200

    res = client.delete(f"/v1/studies/{study_id}/extensions/xpansion")
    assert res.status_code == 200

    if study_type == "variant":
        # Generate the fs
        task_id = client.put(f"/v1/studies/{study_id}/generate").json()
        res = client.get(f"/v1/tasks/{task_id}?wait_for_completion=True")
        assert res.status_code == 200
    assert not expansion_path.exists()

    # Checks generated commands
    if study_type == "variant":
        # todo: make this test evolve for each new xpansion command created
        res = client.get(f"/v1/studies/{study_id}/commands")
        commands_list = res.json()
        assert len(commands_list) == 10
        assert commands_list[0]["action"] == "create_xpansion_configuration"

        assert commands_list[1]["action"] == "create_xpansion_constraint"
        assert commands_list[1]["args"] == {"data": "content_constraints1\n", "filename": "filename_constraints1.txt"}

        assert commands_list[2]["action"] == "create_xpansion_constraint"
        assert commands_list[2]["args"] == {"data": "content_constraints2\n", "filename": "filename_constraints2.txt"}

        assert commands_list[3]["action"] == "create_xpansion_constraint"
        assert commands_list[3]["args"] == {"data": "content_constraints3\n", "filename": "filename_constraints3.txt"}

        assert commands_list[4]["action"] == "remove_xpansion_resource"
        assert commands_list[4]["args"] == {"filename": "filename_constraints1.txt", "resource_type": "constraints"}

        assert commands_list[5]["action"] == "create_xpansion_capacity"
        assert commands_list[5]["args"] == {"filename": "filename_capa1.txt", "matrix": ANY}

        assert commands_list[6]["action"] == "create_xpansion_capacity"
        assert commands_list[6]["args"] == {"filename": "filename_capa2.txt", "matrix": ANY}

        assert commands_list[7]["action"] == "create_xpansion_capacity"
        assert commands_list[7]["args"] == {"filename": "filename_capa3.txt", "matrix": ANY}

        assert commands_list[8]["action"] == "remove_xpansion_resource"
        assert commands_list[8]["args"] == {"filename": "filename_capa1.txt", "resource_type": "capacities"}

        assert commands_list[9]["action"] == "remove_xpansion_configuration"
