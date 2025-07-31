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

from antarest.core.tasks.model import TaskStatus
from tests.integration.utils import wait_task_completion


class TestAdvancedParametersForm:
    """
    Test the end points related to advanced parameters.

    Those tests use the "examples/studies/STA-mini.zip" Study,
    which contains the following areas: ["de", "es", "fr", "it"].
    """

    def test_get_advanced_parameters_values(
        self,
        client: TestClient,
        user_access_token: str,
        internal_study_id: str,
    ):
        """Check `get_advanced_parameters_form_values` end point"""
        res = client.get(
            f"/v1/studies/{internal_study_id}/config/advancedparameters/form",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == HTTPStatus.OK, res.json()
        actual = res.json()
        expected = {
            "accuracyOnCorrelation": "",
            "dayAheadReserveManagement": "global",
            "hydroHeuristicPolicy": "accommodate rule curves",
            "hydroPricingMode": "fast",
            "initialReservoirLevels": "cold start",
            "numberOfCoresMode": "maximum",
            "powerFluctuations": "free modulations",
            "renewableGenerationModelling": "clusters",
            "seedHydroCosts": 9005489,
            "seedInitialReservoirLevels": 10005489,
            "seedSpilledEnergyCosts": 7005489,
            "seedThermalCosts": 8005489,
            "seedTsgenHydro": 2005489,
            "seedTsgenLoad": 1005489,
            "seedTsgenSolar": 4005489,
            "seedTsgenThermal": 3005489,
            "seedTsgenWind": 5489,
            "seedTsnumbers": 5005489,
            "seedUnsuppliedEnergyCosts": 6005489,
            "sheddingPolicy": "shave peaks",
            "unitCommitmentMode": "fast",
        }
        assert actual == expected

    @pytest.mark.parametrize("study_version", [0, 880])
    def test_set_advanced_parameters_values(
        self, client: TestClient, user_access_token: str, internal_study_id: str, study_version: int
    ):
        """Check `set_advanced_parameters_values` end point"""
        obj = {"initialReservoirLevels": "hot start"}
        res = client.put(
            f"/v1/studies/{internal_study_id}/config/advancedparameters/form",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=obj,
        )
        assert res.status_code == HTTPStatus.OK, res.json()
        assert res.json() == {
            "accuracyOnCorrelation": "",
            "accurateShavePeaksIncludeShortTermStorage": None,
            "dayAheadReserveManagement": "global",
            "hydroHeuristicPolicy": "accommodate rule curves",
            "hydroPricingMode": "fast",
            "initialReservoirLevels": "hot start",
            "numberOfCoresMode": "maximum",
            "powerFluctuations": "free modulations",
            "renewableGenerationModelling": "clusters",
            "seedHydroCosts": 9005489,
            "seedInitialReservoirLevels": 10005489,
            "seedSpilledEnergyCosts": 7005489,
            "seedThermalCosts": 8005489,
            "seedTsgenHydro": 2005489,
            "seedTsgenLoad": 1005489,
            "seedTsgenSolar": 4005489,
            "seedTsgenThermal": 3005489,
            "seedTsgenWind": 5489,
            "seedTsnumbers": 5005489,
            "seedUnsuppliedEnergyCosts": 6005489,
            "sheddingPolicy": "shave peaks",
            "unitCommitmentMode": "fast",
        }

        if study_version:
            res = client.put(
                f"/v1/studies/{internal_study_id}/upgrade",
                headers={"Authorization": f"Bearer {user_access_token}"},
                params={"target_version": study_version},
            )
            assert res.status_code == 200, res.json()

            task_id = res.json()
            task = wait_task_completion(client, user_access_token, task_id)
            assert task.status == TaskStatus.COMPLETED, task

        valid_params = "wind, solar"
        res = client.put(
            f"/v1/studies/{internal_study_id}/config/advancedparameters/form",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={"accuracyOnCorrelation": valid_params},
        )
        assert res.status_code in {200, 201}, res.json()

        invalid_params = "fake_correlation, solar"
        res = client.put(
            f"/v1/studies/{internal_study_id}/config/advancedparameters/form",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json={"accuracyOnCorrelation": invalid_params},
        )
        assert res.status_code == 422
        assert res.json()["exception"] == "RequestValidationError"
        assert res.json()["description"] == "Value error, Invalid value: fake_correlation"

        obj = {"unitCommitmentMode": "milp"}
        res = client.put(
            f"/v1/studies/{internal_study_id}/config/advancedparameters/form",
            headers={"Authorization": f"Bearer {user_access_token}"},
            json=obj,
        )
        if study_version:
            assert res.status_code == HTTPStatus.OK, res.json()
        else:
            assert res.status_code == 422
            response = res.json()
            assert response["exception"] == "ValidationError"
            assert "Unit commitment mode `MILP` only exists in v8.8+ studies" in response["description"]
