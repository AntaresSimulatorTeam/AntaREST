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
from io import BytesIO

import pytest
from starlette.testclient import TestClient

from antarest.study.business.arrow_utils import bytes_to_dataframe
from tests.integration.prepare_proxy import PreparerProxy


@pytest.mark.unit_test
class TestLoad:
    @pytest.mark.parametrize("study_type", ["raw", "variant"])
    def test_load(self, client: TestClient, user_access_token: str, study_type: str) -> None:
        client.headers = {"Authorization": f"Bearer {user_access_token}"}  # type: ignore

        preparer = PreparerProxy(client, user_access_token)
        study_id = preparer.create_study("foo", version=880)

        if study_type == "variant":
            study_id = preparer.create_variant(study_id, name="Variant 1")

        area1_id = preparer.create_area(study_id, name="Area1")["id"]

        # Test simple get ARROW

        res = client.get(f"/v1/studies/{study_id}/{area1_id}/load/series")
        assert res.status_code == 200
        assert res.headers["content-type"] == "application/vnd.apache.arrow.file"

        df = bytes_to_dataframe(res.content)

        column_name = ["ts-0"]
        assert column_name == list(df.columns)
        assert df.metadata == {
            "first_week_size": "7",
            "level": "hourly",
            "start_date": "2018-01-01 00:00:00",
            "steps": "8760",
        }
