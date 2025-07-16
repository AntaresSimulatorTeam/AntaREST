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

from http import HTTPStatus

import pytest
from starlette.testclient import TestClient


@pytest.mark.unit_test
class TestConfigGeneralForm:
    """
    Test the end points related to hydraulic correlation.

    Those tests use the "examples/studies/STA-mini.zip" Study,
    which contains the following areas: ["de", "es", "fr", "it"].
    """

    def test_get_general_config(
        self,
        client: TestClient,
        user_access_token: str,
        internal_study_id: str,
    ):
        """Check `get_general_config` end point"""
        res = client.get(
            f"/v1/studies/{internal_study_id}/config/general/form",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == HTTPStatus.OK, res.json()
        actual = res.json()
        expected = {
            "buildingMode": "Custom",
            "filtering": True,
            "firstDay": 1,
            "firstJanuary": "Monday",
            "firstMonth": "january",
            "firstWeekDay": "Monday",
            "horizon": 2030,
            "lastDay": 7,
            "leapYear": False,
            "mcScenario": True,
            "mode": "Adequacy",
            "nbYears": 1,
            "selectionMode": True,
            "simulationSynthesis": True,
            "yearByYear": False,
        }
        assert actual == expected

    def test_set_general_form_values(
        self,
        client: TestClient,
        user_access_token: str,
        internal_study_id: str,
    ):
        """Check `set_general_form_values` end point"""
        obj = {"horizon": 2020}
        res = client.put(
            f"/v1/studies/{internal_study_id}/config/general/form",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=obj,
        )
        assert res.status_code == HTTPStatus.OK, res.json()
        actual = res.json()
        assert actual is None
