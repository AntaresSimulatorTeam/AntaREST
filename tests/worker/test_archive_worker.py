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
from unittest.mock import Mock
from zipfile import ZIP_DEFLATED, ZipFile

from antarest.core.config import Config, StorageConfig, WorkspaceConfig
from antarest.worker.archive_worker import ArchiveWorker
from antarest.worker.worker import WorkerTaskCommand


def test_archive_worker_action(tmp_path: Path):
    workspace_server_mount_point = tmp_path / "other_mount_point"
    archive_worker = ArchiveWorker(
        Mock(),
        "foo",
        tmp_path,
        Config(storage=StorageConfig(workspaces={"foo": WorkspaceConfig(path=workspace_server_mount_point)})),
    )

    zipname = "somezip.zip"
    destname = "unzipped"
    server_zip_file = workspace_server_mount_point / zipname
    server_output = workspace_server_mount_point / destname

    expected_output = tmp_path / "unzipped"
    zip_file = tmp_path / zipname
    with ZipFile(zip_file, "w", ZIP_DEFLATED) as output_data:
        output_data.writestr("matrix.txt", "0\n1\n2")

    assert zip_file.exists()
    assert not expected_output.exists()

    task_info = WorkerTaskCommand(
        task_id="id",
        task_type="unarchive_foo",
        task_args={
            "src": str(server_zip_file),
            "dest": str(server_output),
            "remove_src": True,
        },
    )
    archive_worker._execute_task(task_info)

    assert not zip_file.exists()
    assert expected_output.exists()
    assert (expected_output / "matrix.txt").read_text() == "0\n1\n2"
