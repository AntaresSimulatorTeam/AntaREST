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
from starlette.testclient import TestClient

from antarest.core.tasks.model import TaskStatus
from tests.integration.utils import wait_task_completion


def test_output_archive_and_unarchive_disk_usage(admin_client: TestClient, internal_study_id: str):

    res = admin_client.post(
        f"/v1/studies/{internal_study_id}/copy",
        params={"study_name": "copied_study", "with_outputs": True, "use_task": False},
    )
    assert res.status_code == 201
    copied_study_id = res.json()
    # getting output id in order to archive in
    res_output = admin_client.get(f"/v1/studies/{copied_study_id}/outputs").json()[0]

    # getting current study disk usage to see any difference if the targeted output is archived
    res_current_study_disk_usage = admin_client.get(f"/v1/studies/{copied_study_id}/disk-usage").json()
    assert 3000000 <= res_current_study_disk_usage < 4000000

    # archiving output to see if the study disk usage decreased
    res = admin_client.post(f"/v1/studies/{copied_study_id}/outputs/{res_output['id']}/_archive")
    task_id = res.json()
    assert task_id is not None
    task = wait_task_completion(admin_client, None, task_id)
    assert task.status == TaskStatus.COMPLETED
    res_current_study_disk_usage_after_archive = admin_client.get(f"/v1/studies/{copied_study_id}/disk-usage").json()
    assert res_current_study_disk_usage != res_current_study_disk_usage_after_archive

    # unarchiving output to see if the study disk usage increased
    res = admin_client.post(f"/v1/studies/{copied_study_id}/outputs/{res_output['id']}/_unarchive")
    task_id = res.json()
    assert task_id is not None
    task = wait_task_completion(admin_client, None, task_id)
    assert task.status == TaskStatus.COMPLETED
    res_current_study_disk_usage_after_unarchive = admin_client.get(f"/v1/studies/{copied_study_id}/disk-usage").json()
    assert res_current_study_disk_usage == res_current_study_disk_usage_after_unarchive
