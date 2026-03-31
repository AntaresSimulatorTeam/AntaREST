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
import numpy as np
import pytest
from starlette.testclient import TestClient


def test_get_raw_output_matrix(admin_client: TestClient, internal_study_id: str) -> None:
    client = admin_client

    res = client.get(
        f"/v1/studies/{internal_study_id}/raw",
        params={"path": "output/20201014-1422eco-hello/economy/mc-ind/00001/areas/es/values-annual"},
    )

    assert res.json() == {
        "columns": [
            "OV. COST % Euro % ",
            "OP. COST % Euro % ",
            "MRG. PRICE % Euro % ",
            "CO2 EMIS. % Tons % ",
            "BALANCE % MWh % ",
            "ROW BAL. % MWh % ",
            "PSP % MWh % ",
            "MISC. NDG % MWh % ",
            "LOAD % MWh % ",
            "H. ROR % MWh % ",
            "WIND % MWh % ",
            "SOLAR % MWh % ",
            "NUCLEAR % MWh % ",
            "LIGNITE % MWh % ",
            "COAL % MWh % ",
            "GAS % MWh % ",
            "OIL % MWh % ",
            "MIX. FUEL % MWh % ",
            "MISC. DTG % MWh % ",
            "H. STOR % MWh % ",
            "H. PUMP % MWh % ",
            "H. LEV % % % ",
            "H. INFL % MWh % ",
            "H. OVFL % % % ",
            "H. VAL % Euro/MWh % ",
            "H. COST % Euro % ",
            "UNSP. ENRG % MWh % ",
            "SPIL. ENRG % MWh % ",
            "LOLD % Hours % ",
            "LOLP % % % ",
            "AVL DTG % MWh % ",
            "DTG MRG % MWh % ",
            "MAX MRG % MWh % ",
            "NP COST % Euro % ",
            "NODU %   % ",
        ],
        "data": [
            [
                46452000,
                46452000,
                47.14,
                0,
                0,
                0,
                0,
                0,
                1402800,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                1402800,
                0,
                0,
                pytest.approx(np.nan, nan_ok=True),
                0,
                pytest.approx(np.nan, nan_ok=True),
                pytest.approx(np.nan, nan_ok=True),
                0,
                0,
                0,
                0,
                0,
                3024000,
                1621200,
                1621200,
                0,
                783,
            ]
        ],
        "index": [0],
    }
