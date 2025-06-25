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

import io
import time
from xml.etree import ElementTree

import pytest
from starlette.testclient import TestClient

from tests.integration.studies_blueprint.assets import ASSETS_DIR
from tests.xml_compare import compare_elements


class TestStudyComments:
    """
    This class contains tests related to the following endpoints:

    - GET /v1/studies/{study_id}/comments
    - PUT /v1/studies/{study_id}/comments
    """

    def test_raw_study(
        self,
        client: TestClient,
        user_access_token: str,
        internal_study_id: str,
    ) -> None:
        """
        This test verifies that we can retrieve and modify the comments of a study.
        It also performs performance measurements and analyzes.
        """
        if pytest.FAST_MODE:
            pytest.skip("Skipping test")
        client.headers = {"Authorization": f"Bearer {user_access_token}"}
        # Get the comments of the study and compare with the expected file
        res = client.get(f"/v1/studies/{internal_study_id}/comments")
        assert res.status_code == 200, res.json()
        actual = res.json()
        actual_xml = ElementTree.parse(io.StringIO(actual)).getroot()
        expected_xml = ElementTree.parse(ASSETS_DIR.joinpath("test_comments/raw_study.comments.xml")).getroot()
        assert compare_elements(actual_xml, expected_xml) == ""

        # Ensure the duration is relatively short
        start = time.time()
        res = client.get(f"/v1/studies/{internal_study_id}/comments")
        assert res.status_code == 200, res.json()
        duration = time.time() - start
        assert 0 <= duration <= 0.1, f"Duration is {duration} seconds"

        # Update the comments of the study
        res = client.put(
            f"/v1/studies/{internal_study_id}/comments",
            json={"comments": "<text>Ceci est un commentaire en français.</text>"},
        )
        assert res.status_code == 204, res.json()

        # Get the comments of the study and compare with the expected file
        res = client.get(f"/v1/studies/{internal_study_id}/comments")
        assert res.status_code == 200, res.json()
        assert res.json() == "<text>Ceci est un commentaire en français.</text>"

    def test_variant_study(
        self,
        client: TestClient,
        user_access_token: str,
        internal_study_id: str,
    ) -> None:
        """
        This test verifies that we can retrieve and modify the comments of a VARIANT study.
        It also performs performance measurements and analyzes.
        """
        client.headers = {"Authorization": f"Bearer {user_access_token}"}
        # First, we create a copy of the study, and we convert it to a managed study.
        res = client.post(
            f"/v1/studies/{internal_study_id}/copy",
            params={"study_name": "default", "with_outputs": False, "use_task": False},  # type: ignore
        )
        assert res.status_code == 201, res.json()
        base_study_id = res.json()
        assert base_study_id is not None

        # Then, we create a new variant of the base study
        res = client.post(f"/v1/studies/{base_study_id}/variants", params={"name": "Variant XYZ"})
        assert res.status_code == 200, res.json()  # should be CREATED
        variant_id = res.json()
        assert variant_id is not None

        # Get the comments of the study and compare with the expected file
        res = client.get(f"/v1/studies/{variant_id}/comments")
        assert res.status_code == 200, res.json()
        actual = res.json()
        actual_xml = ElementTree.parse(io.StringIO(actual)).getroot()
        expected_xml = ElementTree.parse(ASSETS_DIR.joinpath("test_comments/raw_study.comments.xml")).getroot()
        assert compare_elements(actual_xml, expected_xml) == ""

        # Ensure the duration is relatively short
        start = time.time()
        res = client.get(f"/v1/studies/{variant_id}/comments")
        assert res.status_code == 200, res.json()
        duration = time.time() - start
        assert 0 <= duration <= 0.3, f"Duration is {duration} seconds"

        # Update the comments of the study
        res = client.put(
            f"/v1/studies/{variant_id}/comments",
            json={"comments": "<text>Ceci est un commentaire en français.</text>"},
        )
        assert res.status_code == 204, res.json()

        # Get the comments of the study and compare with the expected file
        res = client.get(f"/v1/studies/{variant_id}/comments")
        assert res.status_code == 200, res.json()
        assert res.json() == "<text>Ceci est un commentaire en français.</text>"
