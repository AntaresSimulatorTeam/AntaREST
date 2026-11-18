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
import tempfile
from pathlib import Path
from unittest.mock import patch

from starlette.testclient import TestClient

from antarest.core.jwt import DEFAULT_ADMIN_USER
from antarest.core.tasks.model import TaskDTO, TaskStatus
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import current_time
from antarest.login.utils import current_user_context
from antarest.maintenance.tasks.common import BackGroundTaskStatus
from antarest.maintenance.tasks.disk_space_analyzer import disk_space_analysis
from antarest.service_creator import Services
from antarest.study.model import StudyDiskSpaceAnalysis
from antarest.study.repository import StudyDiskSpaceRepository
from antarest.study.service import StudyService


class TestDiskUsage:
    def test_disk_usage_is_read_from_db_and_not_recomputed(
        self, client: TestClient, user_access_token: str, services: Services, internal_study_id: str
    ) -> None:
        client.headers = {"Authorization": f"Bearer {user_access_token}"}

        # Only managed studies are read from the DB (the others are always computed)
        res = client.post(
            f"/v1/studies/{internal_study_id}/copy", params={"study_name": "managed", "use_task": "false"}
        )
        res.raise_for_status()
        study_id: str = res.json()

        # A value which cannot be the real size of the study on the disk
        stored_size = 123_456_789_012
        with db():
            db.session.merge(
                StudyDiskSpaceAnalysis(
                    study_id=study_id, disk_space_bytes=stored_size, last_analysis_date=current_time()
                )
            )
            db.session.commit()

        # Check that the endpoint returns the stored value and does not recompute it
        with patch.object(StudyService, "compute_disk_usage") as compute:
            res = client.get(f"/v1/studies/{study_id}/disk-usage")
            assert res.status_code == 200, res.json()
            assert res.json() == stored_size
            compute.assert_not_called()

        # The stored value is the only source: updating it changes the response
        with db():
            services.study.disk_space_repository.update(study_id, 42, current_time())
        res = client.get(f"/v1/studies/{study_id}/disk-usage")
        assert res.status_code == 200, res.json()
        assert res.json() == 42

    def test_disk_usage_endpoint(
        self,
        client: TestClient,
        user_access_token: str,
        internal_study_id: str,
        output_zip: Path,
        services: Services,
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

        # Ensure a successful response is received and the disk usage is still zero
        # This is because the snapshot creation does not change a lot the size of the study, therefore it does not trigger a recomputation of the disk usage
        res = client.get(f"/v1/studies/{variant_id}/disk-usage")
        assert res.status_code == 200, res.json()
        disk_usage = res.json()
        assert disk_usage == 0

        # Import an output inside the variant
        res = client.post(
            f"/v1/studies/{variant_id}/output?storage_type=V2",
            files={"output": io.BytesIO(output_zip.read_bytes())},
        )
        assert res.status_code == 202, res.json()

        # Run the disk space analysis to compute the disk usage of the variant
        with current_user_context(DEFAULT_ADMIN_USER):
            analysis = disk_space_analysis(
                service=services.study, disk_repo=StudyDiskSpaceRepository(), lock_folder=Path(tempfile.gettempdir())
            )
        assert analysis.status == BackGroundTaskStatus.SUCCESS

        # Calculate the new disk usage
        res = client.get(f"/v1/studies/{variant_id}/disk-usage")
        assert res.status_code == 200, res.json()
        new_disk_usage = res.json()
        output_size = 79450
        # The analysis measures the whole variant: the snapshot (~250 Kio) and the output
        assert 0.1 * 1024 * 1024 + output_size < new_disk_usage < 0.5 * 1024 * 1024 + output_size
