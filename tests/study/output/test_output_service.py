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
import uuid
from pathlib import Path
from unittest.mock import ANY, Mock

import pytest
from helpers import with_admin_user
from storage.conftest import SimpleSyncTaskService

from antarest.core.exceptions import TaskAlreadyRunning
from antarest.core.model import PublicMode, StudyPermissionType
from antarest.core.remote.remote_executor import IRemoteExecutor
from antarest.core.tasks.model import TaskDTO, TaskResult, TaskStatus, TaskType
from antarest.core.tasks.service import ITaskService
from antarest.core.utils.utils import current_time
from antarest.study.model import (
    RawStudy,
    Study,
)
from antarest.study.output.file_output_storage import FileOutputStorage, FileStudyOutputs, IFileOutputsProvider
from antarest.study.output.output_service import IStudyMetadataProvider, OutputService, StudyMetadata
from antarest.study.storage.utils import is_output_archived
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from antarest.worker.archive_worker import ArchiveTaskArgs


def test_is_output_archived(tmp_path: Path) -> None:
    assert not is_output_archived(path_output=Path("fake_path"))
    assert is_output_archived(path_output=Path("fake_path.zip"))

    zipped_output_path = tmp_path / "output.zip"
    zipped_output_path.mkdir(parents=True)
    assert is_output_archived(path_output=zipped_output_path)
    assert is_output_archived(path_output=tmp_path / "output")

    zipped_with_suffix = tmp_path / "output_1.4.3.zip"
    zipped_with_suffix.mkdir(parents=True)
    assert is_output_archived(path_output=zipped_with_suffix)
    assert is_output_archived(path_output=tmp_path / "output_1.4.3")


def _studies_repository(study: Study) -> IStudyMetadataProvider:
    class Impl(IStudyMetadataProvider):
        def get_study_metadata(self, study_id: str) -> StudyMetadata:
            return StudyMetadata(study.id, study.name)

        def assert_permission(self, study_id: str, permission: StudyPermissionType) -> None:
            pass

    return Impl()


def _file_outputs_provider(study: RawStudy) -> IFileOutputsProvider:
    def not_implemented():
        raise NotImplementedError()

    class Impl(IFileOutputsProvider):
        def get_outputs(self, study_id: str) -> FileStudyOutputs:
            return FileStudyOutputs(
                get_file_study=not_implemented,
                outputs_path=Path(study.path) / "output",
                study_workspace=study.workspace,
            )

    return Impl()


@with_admin_user
def test_unarchive_output_for_other_workspace_is_executed_on_remote(
    tmp_path: Path, command_context: CommandContext
) -> None:
    # Prepare services and data
    study_id = str(uuid.uuid4())
    study_name = "My Study"
    study_mock = Mock(
        spec=RawStudy,
        archived=False,
        id=study_id,
        path=tmp_path,
        owner=None,
        groups=[],
        public_mode=PublicMode.NONE,
        workspace="other_workspace",
        to_json_summary=Mock(return_value={"id": study_id, "name": study_name}),
    )
    # The `name` attribute cannot be mocked during creation of the mock object
    # https://stackoverflow.com/a/62552149/1513933
    study_mock.name = study_name

    cache_mock = Mock()
    task_service = SimpleSyncTaskService()  # using a plain task executor to make sure the executor is called before
    # the end
    remote_executor: IRemoteExecutor = Mock(spec=IRemoteExecutor)
    file_outputs_provider = _file_outputs_provider(study_mock)
    output_storage = FileOutputStorage(
        cache=cache_mock, outputs_provider=file_outputs_provider, remote_executor=remote_executor, tmp_dir=tmp_path
    )

    studies_metadata_repository = _studies_repository(study_mock)
    output_service = OutputService(
        matrix_service=Mock(),
        cache=cache_mock,
        file_transfer_manager=Mock(),
        tmp_dir=tmp_path,
        studies_repository=studies_metadata_repository,
        storage=output_storage,
        task_service=task_service,
    )

    output_id = "some-output"
    remote_executor.execute_remote_task.return_value = TaskResult(success=True, message="OK")  # type: ignore
    (tmp_path / "output" / f"{output_id}.zip").mkdir(parents=True, exist_ok=True)

    # Asks for unarchive
    output_service.unarchive_output(study_id, output_id)

    # Check that a remote unarchive task was created
    remote_executor.execute_remote_task.assert_called_once_with(
        "unarchive_other_workspace",
        ArchiveTaskArgs(
            src=str(tmp_path / "output" / f"{output_id}.zip"), dest=str(tmp_path / "output" / output_id)
        ).model_dump(),
    )


@with_admin_user
def test_archive_output_locks(tmp_path: Path, command_context: CommandContext) -> None:
    study_id = str(uuid.uuid4())
    study_name = "My Study"
    study_mock = Mock(
        spec=RawStudy,
        archived=False,
        id=study_id,
        path=tmp_path,
        owner=None,
        groups=[],
        public_mode=PublicMode.NONE,
        workspace="other_workspace",
        to_json_summary=Mock(return_value={"id": study_id, "name": study_name}),
    )
    # The `name` attribute cannot be mocked during creation of the mock object
    # https://stackoverflow.com/a/62552149/1513933
    study_mock.name = study_name

    cache_mock = Mock()
    task_service = Mock(spec=ITaskService)
    file_outputs_provider = _file_outputs_provider(study_mock)
    output_storage = FileOutputStorage(
        cache=cache_mock, outputs_provider=file_outputs_provider, remote_executor=Mock(), tmp_dir=tmp_path
    )

    studies_metadata_repository = _studies_repository(study_mock)
    output_service = OutputService(
        matrix_service=Mock(),
        cache=cache_mock,
        file_transfer_manager=Mock(),
        tmp_dir=tmp_path,
        studies_repository=studies_metadata_repository,
        storage=output_storage,
        task_service=task_service,
    )

    output_zipped = "some-output_zipped"
    output_unzipped = "some-output_unzipped"
    (tmp_path / "output" / output_unzipped).mkdir(parents=True)
    (tmp_path / "output" / f"{output_zipped}.zip").touch()
    task_service.list_tasks.side_effect = [
        [
            TaskDTO(
                id="1",
                name=f"Archive output {study_id}/{output_zipped}",
                status=TaskStatus.PENDING,
                creation_date_utc=str(current_time()),
                type=TaskType.ARCHIVE,
                ref_id=study_id,
            )
        ],
        [
            TaskDTO(
                id="1",
                name=f"Unarchive output {study_name}/{output_zipped} ({study_id})",
                status=TaskStatus.PENDING,
                creation_date_utc=str(current_time()),
                type=TaskType.UNARCHIVE,
                ref_id=study_id,
            )
        ],
        [
            TaskDTO(
                id="1",
                name=f"Archive output {study_id}/{output_unzipped}",
                status=TaskStatus.PENDING,
                creation_date_utc=str(current_time()),
                type=TaskType.ARCHIVE,
                ref_id=study_id,
            )
        ],
        [
            TaskDTO(
                id="1",
                name=f"Unarchive output {study_name}/{output_unzipped} ({study_id})",
                status=TaskStatus.RUNNING,
                creation_date_utc=str(current_time()),
                type=TaskType.UNARCHIVE,
                ref_id=study_id,
            )
        ],
        [],
    ]

    with pytest.raises(TaskAlreadyRunning):
        output_service.unarchive_output(study_id, output_zipped)

    with pytest.raises(TaskAlreadyRunning):
        output_service.unarchive_output(study_id, output_zipped)

    with pytest.raises(TaskAlreadyRunning):
        output_service.archive_output(
            study_id,
            output_unzipped,
        )

    with pytest.raises(TaskAlreadyRunning):
        output_service.archive_output(
            study_id,
            output_unzipped,
        )

    output_service.unarchive_output(study_id, output_zipped)

    task_service.add_task.assert_called_once_with(
        ANY,
        f"Unarchive output {study_name}/{output_zipped} ({study_id})",
        task_type=TaskType.UNARCHIVE,
        ref_id=study_id,
        progress=None,
        custom_event_messages=None,
    )
