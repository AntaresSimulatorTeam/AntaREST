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


class TestNormalization:
    def test_endpoint(self, client: TestClient, internal_study_id: str, user_access_token: str) -> None:
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        ##########################
        # Nominal cases
        ##########################

        ##########################
        # Error cases
        ##########################

        # Ensures we can't normalize an unmanaged study
        res = client.put(f"/v1/studies/{internal_study_id}/normalize")
        assert res.status_code == 422
        result = res.json()
        assert result["exception"] == "NotAManagedStudyException"
        assert result["description"] == f"Study {internal_study_id} is not managed"

        # Ensures we can't normalize a variant study
