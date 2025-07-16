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

from pathlib import Path

from starlette.testclient import TestClient

from antarest.core.tasks.model import TaskDTO, TaskStatus


class TestDiskUsage:
    def test_disk_usage_endpoint(
        self,
        client: TestClient,
        user_access_token: str,
        internal_study_id: str,
        tmp_path: Path,
    ) -> None:
        """
        Verify the functionality of the disk usage endpoint:

        - Ensure a successful response is received.
        - Confirm that the JSON response is an integer which represent a (big enough) directory size.
        """
        disk_usage: int

        user_headers = {"Authorization": f"Bearer {user_access_token}"}
        res = client.get(
            f"/v1/studies/{internal_study_id}/disk-usage",
            headers=user_headers,
        )
        assert res.status_code == 200, res.json()
        disk_usage = res.json()  # currently: 8.75 Mio on Ubuntu
        assert 8 * 1024 * 1024 < disk_usage < 9 * 1024 * 1024

        # Copy the study in managed workspace in order to create a variant
        res = client.post(
            f"/v1/studies/{internal_study_id}/copy",
            headers=user_headers,
            params={"study_name": "somewhere", "use_task": "false"},
        )
        res.raise_for_status()
        parent_id: str = res.json()

        # Create variant of the copied study
        res = client.post(
            f"/v1/studies/{parent_id}/variants",
            headers=user_headers,
            params={"name": "Variant Test"},
        )
        res.raise_for_status()
        variant_id: str = res.json()

        # Ensure a successful response is received even if the variant has no snapshot
        res = client.get(
            f"/v1/studies/{variant_id}/disk-usage",
            headers=user_headers,
        )
        assert res.status_code == 200, res.json()
        disk_usage = res.json()
        assert disk_usage == 0

        # Generate a snapshot for the variant
        res = client.put(
            f"/v1/studies/{variant_id}/generate",
            headers={"Authorization": f"Bearer {user_access_token}"},
            params={"from_scratch": True},
        )
        res.raise_for_status()
        task_id = res.json()

        # Wait for task completion
        res = client.get(f"/v1/tasks/{task_id}", headers=user_headers, params={"wait_for_completion": True})
        assert res.status_code == 200
        task_result = TaskDTO.model_validate(res.json())
        assert task_result.status == TaskStatus.COMPLETED
        assert task_result.result is not None
        assert task_result.result.success

        # Ensure a successful response is received and the disk usage is not zero
        res = client.get(
            f"/v1/studies/{variant_id}/disk-usage",
            headers=user_headers,
        )
        assert res.status_code == 200, res.json()
        disk_usage = res.json()
        # currently: 850 Kio on Ubuntu because the parent study is normalized as it was imported.
        assert 0.1 * 1024 * 1024 < disk_usage < 0.5 * 1024 * 1024

        # Create dummy outputs for the variant
        outputs_dir = tmp_path / "internal_workspace" / variant_id / "output"
        for output in ["20240208-1200eco", "20240208-1300eco"]:
            output_dir = outputs_dir / output
            output_dir.mkdir(parents=True)
            (output_dir / "dummy.txt").write_bytes(b"dummy content")

        # Calculate the new disk usage
        res = client.get(
            f"/v1/studies/{variant_id}/disk-usage",
            headers=user_headers,
        )
        assert res.status_code == 200, res.json()
        new_disk_usage = res.json()
        assert new_disk_usage == disk_usage + 2 * len(b"dummy content")
