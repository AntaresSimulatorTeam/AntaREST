# Copyright (c) 2024, RTE (https://www.rte-france.com)
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
from urllib.parse import urljoin

from starlette.testclient import TestClient

from antarest.study.business.xpansion_management import XpansionCandidateDTO


def _create_area(
    client: TestClient,
    headers: t.Mapping[str, str],
    study_id: str,
    area_name: str,
    *,
    country: str,
) -> str:
    res = client.post(
        f"/v1/studies/{study_id}/areas",
        headers=headers,
        json={"name": area_name, "type": "AREA", "metadata": {"country": country}},
    )
    assert res.status_code in {200, 201}, res.json()
    return t.cast(str, res.json()["id"])


def _create_link(
    client: TestClient,
    headers: t.Mapping[str, str],
    study_id: str,
    src_area_id: str,
    dst_area_id: str,
) -> None:
    res = client.post(
        f"/v1/studies/{study_id}/links",
        headers=headers,
        json={"area1": src_area_id, "area2": dst_area_id},
    )
    assert res.status_code in {200, 201}, res.json()


def test_integration_xpansion(client: TestClient, tmp_path: Path, admin_access_token: str) -> None:
    headers = {"Authorization": f"Bearer {admin_access_token}"}

    res = client.post("/v1/studies", headers=headers, params={"name": "foo", "version": "860"})
    assert res.status_code == 201, res.json()
    study_id = res.json()

    area1_id = _create_area(client, headers, study_id, "area1", country="FR")
    area2_id = _create_area(client, headers, study_id, "area2", country="DE")
    area3_id = _create_area(client, headers, study_id, "area3", country="DE")
    _create_link(client, headers, study_id, area1_id, area2_id)

    res = client.post(f"/v1/studies/{study_id}/extensions/xpansion", headers=headers)
    assert res.status_code in {200, 201}, res.json()

    expansion_path = tmp_path / "internal_workspace" / study_id / "user" / "expansion"
    assert expansion_path.exists()

    # Create a client for Xpansion with the xpansion URL
    xpansion_base_url = f"/v1/studies/{study_id}/extensions/xpansion/"
    xp_client = TestClient(client.app, base_url=urljoin(client.base_url, xpansion_base_url))

    res = xp_client.get("settings", headers=headers)
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

    res = xp_client.put("settings", headers=headers, json={"optimality_gap": 42})
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

    res = xp_client.put("settings", headers=headers, json={"additional-constraints": "missing.txt"})
    assert res.status_code == 404
    err_obj = res.json()
    assert re.search(r"file 'missing.txt' does not exist", err_obj["description"])
    assert err_obj["exception"] == "XpansionFileNotFoundError"

    res = xp_client.put("settings/additional-constraints", headers=headers, params={"filename": "missing.txt"})
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
    res = xp_client.post("resources/constraints", headers=headers, files=files)
    assert res.status_code in {200, 201}
    actual_path = expansion_path / "constraints" / filename_constraints1
    assert actual_path.read_text() == content_constraints1

    files = {
        "file": (
            filename_constraints1,
            io.BytesIO(content_constraints1.encode("utf-8")),
            "image/jpeg",
        ),
    }

    res = xp_client.post("resources/constraints", headers=headers, files=files)
    assert res.status_code == 409
    err_obj = res.json()
    assert re.search(
        rf"File '{filename_constraints1}' already exists",
        err_obj["description"],
        flags=re.IGNORECASE,
    )
    assert err_obj["exception"] == "FileAlreadyExistsError"

    files = {
        "file": (
            filename_constraints2,
            io.BytesIO(content_constraints2.encode("utf-8")),
            "image/jpeg",
        ),
    }
    res = xp_client.post("resources/constraints", headers=headers, files=files)
    assert res.status_code in {200, 201}

    files = {
        "file": (
            filename_constraints3,
            io.BytesIO(content_constraints3.encode("utf-8")),
            "image/jpeg",
        ),
    }
    res = xp_client.post("resources/constraints", headers=headers, files=files)
    assert res.status_code in {200, 201}

    res = xp_client.get(f"resources/constraints/{filename_constraints1}", headers=headers)
    assert res.status_code == 200
    assert res.json() == content_constraints1

    res = xp_client.get("resources/constraints/", headers=headers)
    assert res.status_code == 200
    assert res.json() == [
        filename_constraints1,
        filename_constraints2,
        filename_constraints3,
    ]

    res = xp_client.put(
        "settings/additional-constraints",
        headers=headers,
        params={"filename": filename_constraints1},
    )
    assert res.status_code == 200

    res = xp_client.delete(f"resources/constraints/{filename_constraints1}", headers=headers)
    assert res.status_code == 409
    err_obj = res.json()
    assert re.search(
        rf"File '{filename_constraints1}' is still used",
        err_obj["description"],
        flags=re.IGNORECASE,
    )
    assert err_obj["exception"] == "FileCurrentlyUsedInSettings"

    res = xp_client.put("settings/additional-constraints", headers=headers)
    assert res.status_code == 200

    res = xp_client.delete(f"resources/constraints/{filename_constraints1}", headers=headers)
    assert res.status_code == 200

    candidate1 = {
        "name": "candidate1",
        "link": f"{area1_id} - {area2_id}",
        "annual-cost-per-mw": 1,
        "max-investment": 1.0,
    }
    res = xp_client.post("candidates", headers=headers, json=candidate1)
    assert res.status_code in {200, 201}

    candidate2 = {
        "name": "candidate2",
        "link": f"{area1_id} - {area3_id}",
        "annual-cost-per-mw": 1,
        "max-investment": 1.0,
    }
    res = xp_client.post("candidates", headers=headers, json=candidate2)
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
    res = xp_client.post("candidates", headers=headers, json=candidate3)
    assert res.status_code == 404
    err_obj = res.json()
    assert re.search(
        rf"link from '{area3_id}' to 'non_existent_area' not found",
        err_obj["description"],
        flags=re.IGNORECASE,
    )
    assert err_obj["exception"] == "LinkNotFound"

    filename_capa1 = "filename_capa1.txt"
    filename_capa2 = "filename_capa2.txt"
    filename_capa3 = "filename_capa3.txt"
    content_capa1 = "0"
    content_capa2 = "1"
    content_capa3 = "2"
    files = {
        "file": (
            filename_capa1,
            io.BytesIO(content_capa1.encode("utf-8")),
            "txt/csv",
        )
    }
    res = xp_client.post("resources/capacities", headers=headers, files=files)
    assert res.status_code in {200, 201}
    actual_path = expansion_path / "capa" / filename_capa1
    assert actual_path.read_text() == content_capa1

    res = xp_client.post("resources/capacities", headers=headers, files=files)
    assert res.status_code == 409
    err_obj = res.json()
    assert re.search(
        rf"File '{filename_capa1}' already exists",
        err_obj["description"],
        flags=re.IGNORECASE,
    )
    assert err_obj["exception"] == "FileAlreadyExistsError"

    files = {
        "file": (
            filename_capa2,
            io.BytesIO(content_capa2.encode("utf-8")),
            "txt/csv",
        )
    }
    res = xp_client.post("resources/capacities", headers=headers, files=files)
    assert res.status_code in {200, 201}

    files = {
        "file": (
            filename_capa3,
            io.BytesIO(content_capa3.encode("utf-8")),
            "txt/csv",
        )
    }
    res = xp_client.post("resources/capacities", headers=headers, files=files)
    assert res.status_code in {200, 201}

    # get single capa
    res = xp_client.get(f"resources/capacities/{filename_capa1}", headers=headers)
    assert res.status_code == 200
    assert res.json() == {
        "columns": [0],
        "data": [[0.0]],
        "index": [0],
    }

    res = xp_client.get("resources/capacities", headers=headers)
    assert res.status_code == 200
    assert res.json() == [filename_capa1, filename_capa2, filename_capa3]

    candidate4 = {
        "name": "candidate4",
        "link": f"{area1_id} - {area2_id}",
        "annual-cost-per-mw": 1,
        "max-investment": 1.0,
        "link-profile": filename_capa1,
    }
    res = xp_client.post("candidates", headers=headers, json=candidate4)
    assert res.status_code in {200, 201}

    res = xp_client.get(f"candidates/{candidate1['name']}", headers=headers)
    assert res.status_code == 200
    assert res.json() == XpansionCandidateDTO.parse_obj(candidate1).dict(by_alias=True)

    res = xp_client.get("candidates", headers=headers)
    assert res.status_code == 200
    assert res.json() == [
        XpansionCandidateDTO.parse_obj(candidate1).dict(by_alias=True),
        XpansionCandidateDTO.parse_obj(candidate4).dict(by_alias=True),
    ]

    res = xp_client.delete(f"resources/capacities/{filename_capa1}", headers=headers)
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
    res = xp_client.put(f"candidates/{candidate4['name']}", headers=headers, json=candidate5)
    assert res.status_code == 200

    res = xp_client.delete(f"resources/capacities/{filename_capa1}", headers=headers)
    assert res.status_code == 200

    res = client.delete(f"/v1/studies/{study_id}/extensions/xpansion", headers=headers)
    assert res.status_code == 200

    assert not expansion_path.exists()
