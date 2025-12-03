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
from pathlib import Path

from starlette.testclient import TestClient

from antarest.core.serde.json import from_json
from antarest.core.tasks.model import TaskStatus
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.study.storage.output_model import OutputVariables, OutputVariablesViewsModel
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency
from tests.integration.raw_studies_blueprint.assets import ASSETS_DIR as assets_dir
from tests.integration.utils import wait_task_completion

ASSETS_DIR = assets_dir / "output_variables_list"


def test_get_output_variables_list(client: TestClient, user_access_token: str, internal_study_id: str):
    client.headers = {"Authorization": f"Bearer {user_access_token}"}

    # Checks the endpoint works correctly
    output_id = "20201014-1425eco-goodbye"
    res = client.get(f"/v1/studies/{internal_study_id}/output/{output_id}/variables-list")
    expected_content = from_json((ASSETS_DIR / "res1.json").read_bytes())
    assert expected_content == res.json()

    # Ensures we saved the data inside the DB and that we're still able to read it
    with db():
        db_content: OutputVariables | None = db.session.get(OutputVariables, (internal_study_id, output_id))
        assert db_content is not None
        assert db_content.study_id == internal_study_id
        assert db_content.output_id == output_id
        assert db_content.variables_list_version == 1
        assert db_content.to_model().model_dump(by_alias=True) == expected_content

    # Checks mc-all links work properly as we didn't have any info in the first output
    output_id = "20241807-1540eco-extra-outputs"
    res = client.get(f"/v1/studies/{internal_study_id}/output/{output_id}/variables-list")
    assert res.json()["mcAll"]["links"] == [
        {
            "area1Name": "de",
            "area2Name": "fr",
            "variables": [
                "CONG. FEE (ABS.) EXP",
                "CONG. FEE (ABS.) MAX",
                "CONG. FEE (ABS.) MIN",
                "CONG. FEE (ABS.) STD",
                "CONG. FEE (ALG.) EXP",
                "CONG. FEE (ALG.) MAX",
                "CONG. FEE (ALG.) MIN",
                "CONG. FEE (ALG.) STD",
                "CONG. PROB + VALUES",
                "CONG. PROB - VALUES",
                "FLOW LIN. EXP",
                "FLOW LIN. MAX",
                "FLOW LIN. MIN",
                "FLOW LIN. STD",
                "FLOW QUAD. VALUES",
                "HURDLE COST EXP",
                "HURDLE COST MAX",
                "HURDLE COST MIN",
                "HURDLE COST STD",
                "LOOP FLOW VALUES",
                "MARG. COST EXP",
                "MARG. COST MAX",
                "MARG. COST MIN",
                "MARG. COST STD",
                "UCAP LIN. EXP",
                "UCAP LIN. MAX",
                "UCAP LIN. MIN",
                "UCAP LIN. STD",
            ],
        }
    ]


def test_get_output_variables_list_limit_case(
    client: TestClient, user_access_token: str, internal_study_id: str, tmp_path: Path
) -> None:
    client.headers = {"Authorization": f"Bearer {user_access_token}"}

    # Some areas have a `-` inside their ids. We need to ensure we're able to read their links' related variables
    output_id = "20201014-1425eco-goodbye"
    folder_path = tmp_path / "ext_workspace" / "STA-mini" / "output" / output_id / "economy" / "mc-all" / "links"
    link_path = folder_path / "fr - psp-open"
    link_path.mkdir()
    res = client.get(f"/v1/studies/{internal_study_id}/output/{output_id}/variables-list")
    assert res.status_code == 200


def test_get_output_variables_imagrid_endpoint(client: TestClient, user_access_token: str, internal_study_id: str):
    client.headers = {"Authorization": f"Bearer {user_access_token}"}
    output_id = "20201014-1425eco-goodbye"
    res = client.get(f"/v1/studies/{internal_study_id}/outputs/{output_id}/variables")
    expected_result = {
        "area": [
            "AVL DTG",
            "BALANCE",
            "CO2 EMIS.",
            "COAL",
            "DTG MRG",
            "GAS",
            "H. COST",
            "H. INFL",
            "H. LEV",
            "H. OVFL",
            "H. PUMP",
            "H. ROR",
            "H. STOR",
            "H. VAL",
            "LIGNITE",
            "LOAD",
            "LOLD",
            "LOLP",
            "MAX MRG",
            "MISC. DTG",
            "MISC. NDG",
            "MIX. FUEL",
            "MRG. PRICE",
            "NODU",
            "NP COST",
            "NUCLEAR",
            "OIL",
            "OP. COST",
            "OV. COST",
            "PSP",
            "ROW BAL.",
            "SOLAR",
            "SPIL. ENRG",
            "UNSP. ENRG",
            "WIND",
        ],
        "link": [
            "CONG. FEE (ABS.)",
            "CONG. FEE (ALG.)",
            "CONG. PROB +",
            "CONG. PROB -",
            "FLOW LIN.",
            "FLOW QUAD.",
            "HURDLE COST",
            "LOOP FLOW",
            "MARG. COST",
            "UCAP LIN.",
        ],
    }
    assert res.json() == expected_result


def test_get_output_variables_view(client: TestClient, user_access_token: str, internal_study_id: str):
    client.headers = {"Authorization": f"Bearer {user_access_token}"}
    output_id = "20201014-1425eco-goodbye"
    url = f"/v1/studies/{internal_study_id}/output/{output_id}/variables-views"

    # Areas
    query_params = {"type": "area", "variable_name": "OP. COST", "frequency": "weekly", "area_id": "de"}
    # Ensures asking for the data before it was materialized raises an exception
    res = client.get(f"{url}/data", params=query_params)
    assert res.json() == {
        "description": "The output variables view is not materialized in DB yet",
        "exception": "HTTPException",
    }
    assert res.status_code == 404
    # Materialize the data
    task_id = client.post(f"{url}/materialize", params=query_params).json()
    task = wait_task_completion(client, user_access_token, task_id)
    assert task.status == TaskStatus.COMPLETED
    # Asks for the data. This time, it should succeed.
    res = client.get(f"{url}/data", params=query_params)
    assert res.json() == {"data": [[46452000.0, 46452000.0], [46452000.0, 46452000.0]], "columns": [0, 1]}
    # Try to materialize even if the view is already in the database. Should raise an exception
    res = client.post(f"{url}/materialize", params=query_params)
    assert res.json() == {
        "description": "The output variables view is already materialized in DB",
        "exception": "HTTPException",
    }

    # Thermal clusters
    query_params = {
        "type": "thermal",
        "variable_name": "NODU",
        "frequency": "weekly",
        "area_id": "de",
        "thermal_id": "01_solar",
    }
    task_id = client.post(f"{url}/materialize", params=query_params).json()
    task = wait_task_completion(client, user_access_token, task_id)
    assert task.status == TaskStatus.COMPLETED
    res = client.get(f"{url}/data", params=query_params)
    assert res.json() == {"columns": [0, 1], "data": [[167.0, 167.0], [167.0, 167.0]]}

    # Links
    query_params = {
        "type": "link",
        "variable_name": "FLOW LIN.",
        "frequency": "hourly",
        "area_from_id": "de",
        "area_to_id": "fr",
    }
    task_id = client.post(f"{url}/materialize", params=query_params).json()
    task = wait_task_completion(client, user_access_token, task_id)
    assert task.status == TaskStatus.COMPLETED
    res = client.get(f"{url}/data", params=query_params)
    assert res.json() == {"data": 336 * [[0.0, 0.0]], "columns": [0, 1]}

    # Ensures we saved the data inside the DB and that we're still able to read them
    with db():
        db_content: list[OutputVariablesViewsModel] = db.session.query(OutputVariablesViewsModel).all()
        db_content.sort(key=lambda x: x.last_read)  # Sort for the test
        assert len(db_content) == 3

        first_view = db_content[0]
        assert first_view.study_id == internal_study_id
        assert first_view.output_id == output_id
        assert first_view.area_id == "de"
        assert first_view.frequency == MatrixFrequency.WEEKLY
        assert first_view.variable_name == "OP. COST"

        second_view = db_content[1]
        assert first_view.study_id == internal_study_id
        assert first_view.output_id == output_id
        assert second_view.area_id == "de"
        assert second_view.thermal_id == "01_solar"
        assert second_view.frequency == MatrixFrequency.WEEKLY
        assert second_view.variable_name == "NODU"

        third_view = db_content[2]
        assert first_view.study_id == internal_study_id
        assert first_view.output_id == output_id
        assert third_view.area_from_id == "de"
        assert third_view.area_to_id == "fr"
        assert third_view.frequency == MatrixFrequency.HOURLY
        assert third_view.variable_name == "FLOW LIN."
