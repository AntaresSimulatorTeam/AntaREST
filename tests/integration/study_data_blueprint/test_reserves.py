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

from io import BytesIO
from pathlib import Path
from typing import Any
from zipfile import ZipFile

import numpy as np
import pytest
import yaml
from starlette.testclient import TestClient

from tests.integration.assets import ASSETS_DIR
from tests.test_helpers.download import download_to_file


@pytest.mark.parametrize("storage_mode", ["filesystem", "database"])
def test_reserve_writes_rejected_before_10_2(admin_client: TestClient, storage_mode: str) -> None:
    client = admin_client
    res = client.post("/v1/studies", params={"name": "Legacy", "version": "9.3", "storage_mode": storage_mode})
    assert res.status_code == 201, res.text
    study_id = res.json()
    res = client.post(f"/v1/studies/{study_id}/areas", json={"name": "fr", "type": "AREA"})
    assert res.status_code == 200, res.text
    base = f"/v1/studies/{study_id}/areas/fr/reserves"
    requests: list[tuple[str, str, Any]] = [
        ("POST", "", {"name": "R1", "type": "up"}),
        ("DELETE", "", ["r1"]),
        ("PUT", "/global-parameters", {"energyActivationRatioUp": 0.5}),
    ]
    for asset in ("thermals", "storages", "hydro"):
        requests.append(("PUT", f"/certifications/{asset}", {}))
        requests.append(("PUT", f"/symmetries/{asset}", [] if asset == "hydro" else {}))
    for method, path, body in requests:
        res = client.request(method, f"{base}{path}", json=body)
        assert res.status_code == 422, (method, path, res.text)
        assert res.json()["exception"] == "ValidationError"
        assert "10.2" in res.json()["description"]

    # The legacy reserve matrix remains usable on older studies.
    values = [[1, 2, 3, 4]] * 8760
    res = client.post(f"/v1/studies/{study_id}/raw", params={"path": "input/reserves/fr"}, json=values)
    assert res.status_code == 200, res.text
    res = client.get(f"/v1/studies/{study_id}/raw", params={"path": "input/reserves/fr"})
    assert res.status_code == 200, res.text
    assert res.json()["data"] == values


@pytest.mark.parametrize("storage_mode", ["filesystem", "database"])
@pytest.mark.parametrize("variant", [False, True])
def test_export_simple_10_2_study(admin_client: TestClient, storage_mode: str, variant: bool, tmp_path: Path) -> None:
    client = admin_client
    res = client.post("/v1/studies", params={"name": "Simple 10.2", "version": "10.2", "storage_mode": storage_mode})
    assert res.status_code == 201, res.text
    study_id = res.json()
    for area_id in ("de", "fr"):
        res = client.post(f"/v1/studies/{study_id}/areas", json={"name": area_id, "type": "AREA"})
        assert res.status_code == 200, res.text
    if variant:
        res = client.post(f"/v1/studies/{study_id}/variants", params={"name": "Variant 10.2"})
        assert res.is_success, res.text
        study_id = res.json()

    res = client.get(f"/v1/studies/{study_id}/export")
    assert res.status_code == 200, res.text
    archive_path = tmp_path / "simple.zip"
    download_to_file(client, res.json()["file"]["id"], archive_path)
    with ZipFile(archive_path) as archive:
        for area_id in ("de", "fr"):
            assert archive.read(f"input/reserves/{area_id}.txt") == b""
            assert f"input/reserves/{area_id}/reserves.yml" in archive.namelist()


@pytest.mark.parametrize("storage_mode", ["filesystem", "database"])
def test_reference_reserves_import_edit_export(admin_client: TestClient, storage_mode: str, tmp_path: Path) -> None:
    """Exercise the simulator's symmetry_test_3_LT reference study through the API.

    Fixture source (Desktop.ini omitted):
    https://github.com/AntaresSimulatorTeam/Antares_Simulator_Tests_NR/tree/
    96a4fc36c704bbeeb0f45ae9e0033fcd3a55446e/reserves-tests/symmetry_test_3_LT
    """
    client = admin_client
    res = client.post(
        "/v1/studies/_import",
        params={"storage_mode": storage_mode},
        files={"study": ("reference.zip", (ASSETS_DIR / "symmetry_test_3_LT.zip").read_bytes())},
    )
    assert res.status_code == 201, res.text
    study_id = res.json()
    base = f"/v1/studies/{study_id}/areas/france/reserves"

    res = client.get(base)
    assert res.status_code == 200, res.text
    assert {r["id"]: r["failureCost"] for r in res.json()} == {"res_1_up": 500, "res_2_up": 400}

    res = client.get(f"{base}/certifications/hydro")
    assert res.status_code == 200, res.text
    certifications = res.json()
    assert certifications["res_1_up"]["maxRelease"] == 15
    assert certifications["res_2_up"]["maxRelease"] == 30
    res = client.get(f"{base}/symmetries/hydro")
    assert res.status_code == 200, res.text
    assert res.json() == [["res_1_up", "res_2_up"]]

    # Both the legacy matrix and the new reserve needs must remain accessible.
    for path, shape in (("input/reserves/france.txt", (8760, 4)), ("input/reserves/france/res_1_up", (8760, 1))):
        res = client.get(f"/v1/studies/{study_id}/raw", params={"path": path})
        assert res.status_code == 200, res.text
        assert np.asarray(res.json()["data"]).shape == shape

    res = client.put(f"{base}/global-parameters", json={"energyActivationRatioUp": 0.5})
    assert res.status_code == 200, res.text
    res = client.get(f"{base}/global-parameters")
    assert res.status_code == 200, res.text
    assert res.json()["energyActivationRatioUp"] == 0.5

    certifications["res_1_up"]["maxRelease"] = 20
    res = client.put(f"{base}/certifications/hydro", json=certifications)
    assert res.status_code == 200, res.text
    res = client.get(f"{base}/certifications/hydro")
    assert res.status_code == 200, res.text
    assert res.json() == certifications
    res = client.put(f"{base}/symmetries/hydro", json=[["res_1_up", "res_2_up"]])
    assert res.status_code == 200, res.text
    res = client.get(f"{base}/symmetries/hydro")
    assert res.status_code == 200, res.text
    assert res.json() == [["res_1_up", "res_2_up"]]

    res = client.get(f"/v1/studies/{study_id}/export")
    assert res.status_code == 200, res.text
    archive_path = tmp_path / "export.zip"
    download_to_file(client, res.json()["file"]["id"], archive_path)
    with ZipFile(archive_path) as archive:
        assert archive.read("input/reserves/france.txt") == b""
        reserves = yaml.safe_load(archive.read("input/reserves/france/reserves.yml"))
        assert {r["name"] for r in reserves["reserves"]} == {"Res_1_up", "Res_2_up"}
        assert reserves["globalparameters"]["energy-activation-ratio-up"] == 0.5
        participations = yaml.safe_load(archive.read("input/hydro/reserves/france/reserve-participations.yml"))
        assert {c["reserve"]: c["max-release"] for c in participations["participations"]["certifications"]} == {
            "res_1_up": 20,
            "res_2_up": 30,
        }
        assert participations["participations"]["symmetries"] == [{"reserves": ["res_1_up", "res_2_up"]}]
        with ZipFile(ASSETS_DIR / "symmetry_test_3_LT.zip") as reference:
            for reserve_id in ("res_1_up", "res_2_up"):
                path = f"input/reserves/france/{reserve_id}.txt"
                np.testing.assert_array_equal(
                    np.loadtxt(BytesIO(archive.read(path))), np.loadtxt(BytesIO(reference.read(path)))
                )

    res = client.delete(f"/v1/studies/{study_id}/areas/france")
    assert res.status_code == 200, res.text
    res = client.get(f"/v1/studies/{study_id}/export")
    assert res.status_code == 200, res.text
    download_to_file(client, res.json()["file"]["id"], tmp_path / "without_area.zip")
    with ZipFile(tmp_path / "without_area.zip") as archive:
        assert not any(path.startswith("input/reserves/france") for path in archive.namelist())
