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

import json
import sys
import time

from starlette.testclient import TestClient

from tests.integration.studies_blueprint.assets import ASSETS_DIR


def _compare_resource_file(actual, res_path):
    # note: private data are masked in the resource file
    masked = dict.fromkeys(["study_path", "path", "output_path", "study_id"], "DUMMY_VALUE")
    actual.update(masked)
    if res_path.exists():
        # Compare the actual synthesis with the expected one
        expected = json.loads(res_path.read_text())
        assert actual == expected
    else:
        # Update the resource file with the actual synthesis (a git commit is required)
        res_path.parent.mkdir(parents=True, exist_ok=True)
        res_path.write_text(json.dumps(actual, indent=2, ensure_ascii=False))
        print(f"Resource file '{res_path}' must be committed.", file=sys.stderr)


class TestStudySynthesis:
    """
    This class contains tests related to the following endpoints:

    - GET /v1/studies/{study_id}/synthesis
    """

    def test_raw_study(
        self,
        client: TestClient,
        user_access_token: str,
        internal_study_id: str,
    ) -> None:
        """
        This test verifies that we can retrieve the synthesis of a study.
        It also performs performance measurements and analyzes.
        """

        # Get the synthesis of the study and compare with the expected file
        res = client.get(
            f"/v1/studies/{internal_study_id}/synthesis",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200, res.json()
        actual = res.json()
        res_path = ASSETS_DIR.joinpath("test_synthesis/raw_study.synthesis.json")
        _compare_resource_file(actual, res_path)

        # Ensure the duration is relatively short
        start = time.time()
        res = client.get(
            f"/v1/studies/{internal_study_id}/synthesis",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200, res.json()
        duration = time.time() - start
        assert 0 <= duration <= 0.3, f"Duration is {duration} seconds"

    def test_variant_study(
        self,
        client: TestClient,
        user_access_token: str,
        internal_study_id: str,
    ) -> None:
        """
        This test verifies that we can retrieve and modify the synthesis of a VARIANT study.
        It also performs performance measurements and analyzes.
        """
        # First, we create a copy of the study, and we convert it to a managed study.
        res = client.post(
            f"/v1/studies/{internal_study_id}/copy",
            headers={"Authorization": f"Bearer {user_access_token}"},
            params={"study_name": "default", "with_outputs": False, "use_task": False},  # type: ignore
        )
        assert res.status_code == 201, res.json()
        base_study_id = res.json()
        assert base_study_id is not None

        # Then, we create a new variant of the base study
        res = client.post(
            f"/v1/studies/{base_study_id}/variants",
            headers={"Authorization": f"Bearer {user_access_token}"},
            params={"name": "Variant XYZ"},
        )
        assert res.status_code == 200, res.json()  # should be CREATED
        variant_id = res.json()
        assert variant_id is not None

        # Get the synthesis of the study and compare with the expected file
        res = client.get(
            f"/v1/studies/{variant_id}/synthesis",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200, res.json()
        actual = res.json()
        res_path = ASSETS_DIR.joinpath("test_synthesis/variant_study.synthesis.json")
        _compare_resource_file(actual, res_path)

        # Ensure the duration is relatively short
        start = time.time()
        res = client.get(
            f"/v1/studies/{variant_id}/synthesis",
            headers={"Authorization": f"Bearer {user_access_token}"},
        )
        assert res.status_code == 200, res.json()
        duration = time.time() - start
        assert 0 <= duration <= 0.2, f"Duration is {duration} seconds"
