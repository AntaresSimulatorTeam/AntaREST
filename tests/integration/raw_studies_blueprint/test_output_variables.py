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


def test_get_output_variables_imagrid_endpoint(client: TestClient, user_access_token: str, internal_study_id: str):
    client.headers = {"Authorization": f"Bearer {user_access_token}"}
    output_id = "20201014-1425eco-goodbye"
    res = client.get(f"/v1/studies/{internal_study_id}/outputs/{output_id}/variables")
    expected_result = {
        "area": [
            "OV. COST",
            "OP. COST",
            "MRG. PRICE",
            "CO2 EMIS.",
            "BALANCE",
            "ROW BAL.",
            "PSP",
            "MISC. NDG",
            "LOAD",
            "H. ROR",
            "WIND",
            "SOLAR",
            "NUCLEAR",
            "LIGNITE",
            "COAL",
            "GAS",
            "OIL",
            "MIX. FUEL",
            "MISC. DTG",
            "H. STOR",
            "H. PUMP",
            "H. LEV",
            "H. INFL",
            "H. OVFL",
            "H. VAL",
            "H. COST",
            "UNSP. ENRG",
            "SPIL. ENRG",
            "LOLD",
            "LOLP",
            "AVL DTG",
            "DTG MRG",
            "MAX MRG",
            "NP COST",
            "NODU",
        ],
        "link": [
            "FLOW LIN.",
            "UCAP LIN.",
            "LOOP FLOW",
            "FLOW QUAD.",
            "CONG. FEE (ALG.)",
            "CONG. FEE (ABS.)",
            "MARG. COST",
            "CONG. PROB +",
            "CONG. PROB -",
            "HURDLE COST",
        ],
    }
    assert res.json() == expected_result
