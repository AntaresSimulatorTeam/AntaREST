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

from antarest.core.serde.json import from_json
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.study.storage.output_model import OutputVariables
from tests.integration.raw_studies_blueprint.assets import ASSETS_DIR as assets_dir

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


def test_get_output_variables_list_other_output(client: TestClient, user_access_token: str, internal_study_id: str):
    client.headers = {"Authorization": f"Bearer {user_access_token}"}

    # Checks the endpoint works correctly
    output_id = "20241807-1540eco-extra-outputs"
    res = client.get(f"/v1/studies/{internal_study_id}/output/{output_id}/variables-list")
    print(res.json()["mcAll"]["links"])


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
