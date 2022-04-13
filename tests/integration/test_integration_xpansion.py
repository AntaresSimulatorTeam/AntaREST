from io import StringIO
from pathlib import Path

from fastapi import FastAPI
from starlette.testclient import TestClient

from antarest.study.business.area_management import AreaType
from antarest.study.business.xpansion_management import XpansionCandidateDTO


def test_integration_xpansion(app: FastAPI, tmp_path: str):
    client = TestClient(app, raise_server_exceptions=False)
    res = client.post(
        "/v1/login", json={"username": "admin", "password": "admin"}
    )
    admin_credentials = res.json()
    headers = {"Authorization": f'Bearer {admin_credentials["access_token"]}'}

    created = client.post(
        "/v1/studies?name=foo",
        headers=headers,
    )
    study_id = created.json()

    xpansion_base_url = f"/v1/studies/{study_id}/extensions/xpansion"

    filename_constraints1 = "filename_constraints1.txt"
    filename_constraints2 = "filename_constraints2.txt"
    filename_constraints3 = "filename_constraints3.txt"
    content_constraints1 = "content_constraints1\n"
    content_constraints2 = "content_constraints2\n"
    content_constraints3 = "content_constraints3\n"
    area1_name = "area1"
    area2_name = "area2"
    area3_name = "area3"

    client.post(
        f"/v1/studies/{study_id}/areas",
        headers=headers,
        json={
            "name": area1_name,
            "type": AreaType.AREA.value,
            "metadata": {"country": "FR"},
        },
    )
    client.post(
        f"/v1/studies/{study_id}/areas",
        headers=headers,
        json={
            "name": area2_name,
            "type": AreaType.AREA.value,
            "metadata": {"country": "DE"},
        },
    )
    client.post(
        f"/v1/studies/{study_id}/areas",
        headers=headers,
        json={
            "name": area3_name,
            "type": AreaType.AREA.value,
            "metadata": {"country": "DE"},
        },
    )

    client.post(
        f"/v1/studies/{study_id}/links",
        headers=headers,
        json={
            "area1": area1_name,
            "area2": area2_name,
        },
    )

    # Xpansion
    res = client.post(
        xpansion_base_url,
        headers=headers,
    )
    assert res.status_code == 200

    assert (
        Path(tmp_path) / "internal_workspace" / study_id / "user" / "expansion"
    ).exists()

    res = client.get(
        f"{xpansion_base_url}/settings",
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json() == {
        "additional-constraints": None,
        "ampl.presolve": None,
        "ampl.solve_bounds_frequency": None,
        "ampl.solver": None,
        "cut-type": None,
        "master": "integer",
        "max_iteration": "inf",
        "optimality_gap": 1.0,
        "relative_gap": 1e-12,
        "relaxed-optimality-gap": None,
        "solver": "Cbc",
        "uc_type": "expansion_fast",
        "yearly-weights": None,
    }

    res = client.put(
        f"{xpansion_base_url}/settings",
        headers=headers,
        json={"optimality_gap": 42},
    )
    assert res.status_code == 200
    assert res.json() == {
        "additional-constraints": None,
        "ampl.presolve": None,
        "ampl.solve_bounds_frequency": None,
        "ampl.solver": None,
        "cut-type": None,
        "master": "integer",
        "max_iteration": None,
        "optimality_gap": 42.0,
        "relative_gap": None,
        "relaxed-optimality-gap": None,
        "solver": None,
        "uc_type": "expansion_fast",
        "yearly-weights": None,
    }

    res = client.put(
        f"{xpansion_base_url}/settings",
        headers=headers,
        json={"additional-constraints": 42},
    )
    assert res.status_code == 404

    res = client.put(
        f"{xpansion_base_url}/settings/additional-constraints?filename=42",
        headers=headers,
    )
    assert res.status_code == 404

    files = {
        "file": (
            filename_constraints1,
            StringIO(content_constraints1),
            "image/jpeg",
        )
    }
    res = client.post(
        f"{xpansion_base_url}/constraints",
        headers=headers,
        files=files,
    )
    assert res.status_code == 200
    assert (
        tmp_path
        / "internal_workspace"
        / study_id
        / "user"
        / "expansion"
        / filename_constraints1
    ).open().read() == content_constraints1

    files = {
        "file": (
            filename_constraints1,
            StringIO(content_constraints1),
            "image/jpeg",
        ),
    }

    res = client.post(
        f"{xpansion_base_url}/constraints",
        headers=headers,
        files=files,
    )
    assert res.status_code == 409

    files = {
        "file": (
            filename_constraints2,
            StringIO(content_constraints2),
            "image/jpeg",
        ),
    }
    res = client.post(
        f"{xpansion_base_url}/constraints",
        headers=headers,
        files=files,
    )

    files = {
        "file": (
            filename_constraints3,
            StringIO(content_constraints3),
            "image/jpeg",
        ),
    }
    res = client.post(
        f"{xpansion_base_url}/constraints",
        headers=headers,
        files=files,
    )
    assert res.status_code == 200

    res = client.get(
        f"{xpansion_base_url}/constraints/{filename_constraints1}",
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json() == content_constraints1

    res = client.get(
        f"{xpansion_base_url}/constraints/",
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json() == [
        filename_constraints1,
        filename_constraints2,
        filename_constraints3,
    ]

    res = client.put(
        f"{xpansion_base_url}/settings/additional-constraints?filename={filename_constraints1}",
        headers=headers,
    )
    assert res.status_code == 200

    res = client.delete(
        f"{xpansion_base_url}/constraints/{filename_constraints1}",
        headers=headers,
    )
    assert res.status_code == 409

    res = client.put(
        f"{xpansion_base_url}/settings/additional-constraints",
        headers=headers,
    )
    assert res.status_code == 200

    res = client.delete(
        f"{xpansion_base_url}/constraints/{filename_constraints1}",
        headers=headers,
    )
    assert res.status_code == 200

    candidate1 = {
        "name": "candidate1",
        "link": f"{area1_name} - {area2_name}",
        "annual-cost-per-mw": 1,
        "max-investment": 1.0,
    }
    res = client.post(
        f"{xpansion_base_url}/candidates", headers=headers, json=candidate1
    )
    assert res.status_code == 200

    candidate2 = {
        "name": "candidate2",
        "link": f"{area1_name} - {area3_name}",
        "annual-cost-per-mw": 1,
        "max-investment": 1.0,
    }
    res = client.post(
        f"{xpansion_base_url}/candidates", headers=headers, json=candidate2
    )
    assert res.status_code == 404

    candidate3 = {
        "name": "candidate3",
        "link": f"non_existent_area - {area3_name}",
        "annual-cost-per-mw": 1,
        "max-investment": 1.0,
    }
    res = client.post(
        f"{xpansion_base_url}/candidates", headers=headers, json=candidate3
    )
    assert res.status_code == 404

    filename_capa1 = "filename_capa1.txt"
    filename_capa2 = "filename_capa2.txt"
    filename_capa3 = "filename_capa3.txt"
    content_capa1 = "0"
    content_capa2 = "1"
    content_capa3 = "2"
    files = {
        "file": (
            filename_capa1,
            StringIO(content_capa1),
            "txt/csv",
        )
    }
    res = client.post(
        f"{xpansion_base_url}/capacities",
        headers=headers,
        files=files,
    )
    assert res.status_code == 200
    assert (
        tmp_path
        / "internal_workspace"
        / study_id
        / "user"
        / "expansion"
        / "capa"
        / filename_capa1
    ).open().read() == content_capa1

    res = client.post(
        f"{xpansion_base_url}/capacities",
        headers=headers,
        files=files,
    )
    assert res.status_code == 409

    files = {
        "file": (
            filename_capa2,
            StringIO(content_capa2),
            "txt/csv",
        )
    }
    res = client.post(
        f"{xpansion_base_url}/capacities",
        headers=headers,
        files=files,
    )
    assert res.status_code == 200

    files = {
        "file": (
            filename_capa3,
            StringIO(content_capa3),
            "txt/csv",
        )
    }
    res = client.post(
        f"{xpansion_base_url}/capacities",
        headers=headers,
        files=files,
    )
    assert res.status_code == 200

    # get single capa
    res = client.get(
        f"{xpansion_base_url}/capacities/{filename_capa1}",
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json() == {
        "columns": [0],
        "data": [[0.0]],
        "index": [0],
    }

    res = client.get(
        f"{xpansion_base_url}/capacities",
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json() == [filename_capa1, filename_capa2, filename_capa3]

    candidate4 = {
        "name": "candidate4",
        "link": f"{area1_name} - {area2_name}",
        "annual-cost-per-mw": 1,
        "max-investment": 1.0,
        "link-profile": filename_capa1,
    }
    res = client.post(
        f"{xpansion_base_url}/candidates", headers=headers, json=candidate4
    )
    assert res.status_code == 200

    res = client.get(
        f"{xpansion_base_url}/candidates/{candidate1['name']}",
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json() == XpansionCandidateDTO.parse_obj(candidate1).dict(
        by_alias=True
    )

    res = client.get(
        f"{xpansion_base_url}/candidates",
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json() == [
        XpansionCandidateDTO.parse_obj(candidate1).dict(by_alias=True),
        XpansionCandidateDTO.parse_obj(candidate4).dict(by_alias=True),
    ]

    res = client.delete(
        f"{xpansion_base_url}/capacities/{filename_capa1}",
        headers=headers,
    )
    assert res.status_code == 409

    candidate5 = {
        "name": "candidate4",
        "link": f"{area1_name} - {area2_name}",
        "annual-cost-per-mw": 1,
        "max-investment": 1.0,
    }
    res = client.put(
        f"{xpansion_base_url}/candidates/{candidate4['name']}",
        headers=headers,
        json=candidate5,
    )
    assert res.status_code == 200

    res = client.delete(
        f"{xpansion_base_url}/capacities/{filename_capa1}",
        headers=headers,
    )
    assert res.status_code == 200

    res = client.delete(
        f"/v1/studies/{study_id}/extensions/xpansion",
        headers=headers,
    )
    assert res.status_code == 200

    assert not (
        Path(tmp_path) / "internal_workspace" / study_id / "user" / "expansion"
    ).exists()
