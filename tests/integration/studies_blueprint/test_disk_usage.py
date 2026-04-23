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
import io
from pathlib import Path

from starlette.testclient import TestClient

from antarest.core.tasks.model import TaskDTO, TaskStatus


class TestDiskUsage:
    def test_disk_usage_endpoint(
        self, client: TestClient, user_access_token: str, internal_study_id: str, tmp_path: Path, output_zip: Path
    ) -> None:
        """
        Verify the functionality of the disk usage endpoint:

        - Ensure a successful response is received.
        - Confirm that the JSON response is an integer which represent a (big enough) directory size.
        """
        disk_usage: int

        client.headers = {"Authorization": f"Bearer {user_access_token}"}
        res = client.get(f"/v1/studies/{internal_study_id}/disk-usage")
        assert res.status_code == 200, res.json()
        disk_usage = res.json()  # currently: 8.75 Mio on Ubuntu
        assert 8 * 1024 * 1024 < disk_usage < 9 * 1024 * 1024

        # Copy the study in managed workspace in order to create a variant
        res = client.post(
            f"/v1/studies/{internal_study_id}/copy", params={"study_name": "somewhere", "use_task": "false"}
        )
        res.raise_for_status()
        parent_id: str = res.json()

        # Create variant of the copied study
        res = client.post(f"/v1/studies/{parent_id}/variants", params={"name": "Variant Test"})
        res.raise_for_status()
        variant_id: str = res.json()

        # Ensure a successful response is received even if the variant has no snapshot
        res = client.get(f"/v1/studies/{variant_id}/disk-usage")
        assert res.status_code == 200, res.json()
        disk_usage = res.json()
        assert disk_usage == 0

        # Generate a snapshot for the variant
        res = client.put(f"/v1/studies/{variant_id}/generate", params={"from_scratch": True})
        res.raise_for_status()
        task_id = res.json()

        # Wait for task completion
        res = client.get(f"/v1/tasks/{task_id}", params={"wait_for_completion": True})
        assert res.status_code == 200
        task_result = TaskDTO.model_validate(res.json())
        assert task_result.status == TaskStatus.COMPLETED
        assert task_result.result is not None
        assert task_result.result.success

        # Ensure a successful response is received and the disk usage is not zero
        res = client.get(f"/v1/studies/{variant_id}/disk-usage")
        assert res.status_code == 200, res.json()
        disk_usage = res.json()
        # currently: 850 Kio on Ubuntu because the parent study is normalized as it was imported.
        assert 0.1 * 1024 * 1024 < disk_usage < 0.5 * 1024 * 1024

        # Import an output inside the variant
        res = client.post(
            f"/v1/studies/{variant_id}/output?storage_type=V2",
            files={"output": io.BytesIO(output_zip.read_bytes())},
        )
        assert res.status_code == 202, res.json()

        # Calculate the new disk usage
        res = client.get(f"/v1/studies/{variant_id}/disk-usage")
        assert res.status_code == 200, res.json()
        new_disk_usage = res.json()
        assert new_disk_usage == disk_usage + 2 * len(b"dummy content")
