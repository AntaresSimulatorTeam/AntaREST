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
import zipfile
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from unittest.mock import ANY, Mock

import pytest
from typing_extensions import override

from antarest.core.exceptions import OutputAlreadyExists, TaskAlreadyRunning
from antarest.core.model import PublicMode, StudyPermissionType
from antarest.core.remote.remote_executor import IRemoteExecutor
from antarest.core.tasks.model import TaskDTO, TaskResult, TaskStatus, TaskType
from antarest.core.tasks.service import ITaskService
from antarest.core.utils.utils import current_time
from antarest.output.dbmodel import Output
from antarest.output.service import IStudyMetadataProvider, OutputService, StudyMetadata
from antarest.output.storage.file.abstract_storage import FileStudyOutputs, IFileOutputsProvider
from antarest.output.storage.file.in_study import InStudyFileOutputStorage
from antarest.output.storage.output_storage import IOutputStorage, OutputMetadata, OutputStorageType
from antarest.study.model import (
    RawStudy,
    StorageMode,
    Study,
)
from antarest.study.storage.utils import is_output_archived
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from antarest.worker.archive_worker import ArchiveTaskArgs
from tests.helpers import with_admin_user
from tests.storage.conftest import SimpleSyncTaskService


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
        @override
        def get_study_metadata(self, study_id: str) -> StudyMetadata:
            assert study.name is not None
            return StudyMetadata(study.id, study.name, study.storage_mode)

        @override
        def assert_permission(self, study_id: str, permission: StudyPermissionType) -> None:
            pass

    return Impl()


def _file_outputs_provider(study: RawStudy) -> IFileOutputsProvider:
    def not_implemented() -> None:
        raise NotImplementedError()

    class Impl(IFileOutputsProvider):
        @override
        def get_outputs(self, study_id: str) -> FileStudyOutputs:
            assert study.path is not None
            return FileStudyOutputs(outputs_path=Path(study.path) / "output", study_workspace=study.workspace)

    return Impl()


@with_admin_user
@pytest.mark.parametrize("success", [False, True])
def test_unarchive_output_for_other_workspace_is_executed_on_remote(
    tmp_path: Path, command_context: CommandContext, success: bool
) -> None:
    # Prepare services and data
    workspace_name = "other_workspace"
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
        workspace=workspace_name,
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
    output_storage = InStudyFileOutputStorage(
        cache=cache_mock,
        config=Mock(),
        outputs_provider=file_outputs_provider,
        remote_executor=remote_executor,
        repository=Mock(),
    )

    studies_metadata_repository = _studies_repository(study_mock)
    output_repository = Mock()
    output_service = OutputService(
        matrix_service=Mock(),
        file_transfer_manager=Mock(),
        tmp_dir=tmp_path,
        studies_repository=studies_metadata_repository,
        storages=[output_storage],
        task_service=task_service,
        output_repository=output_repository,
    )

    output_id = "some-output"
    assert isinstance(remote_executor.execute_remote_task, Mock)
    remote_executor.execute_remote_task.return_value = TaskResult(success=success, message="result")
    output_dir = Path(study_mock.path) / "output"
    output_dir.mkdir()
    with zipfile.ZipFile(tmp_path / "output" / f"{output_id}.zip", "w") as zf:
        zf.writestr("fake-file", "")

    # Asks for unarchive
    if success:
        output_service.unarchive_output(study_id, output_id)
        output_repository.save_unarchiving_date.assert_called_once_with(study_id, output_id, ANY)
    else:
        with pytest.raises(RuntimeError, match="result"):
            output_service.unarchive_output(study_id, output_id)
        output_repository.save_unarchiving_date.assert_not_called()

    # Check that a remote unarchive task was created
    remote_executor.execute_remote_task.assert_called_once_with(
        f"unarchive_{workspace_name}",
        ArchiveTaskArgs(
            src=str(tmp_path / "output" / f"{output_id}.zip"), dest=str(tmp_path / "output" / output_id)
        ).model_dump(),
    )


@pytest.mark.parametrize("storage_type", list(OutputStorageType))
@pytest.mark.parametrize("success", [False, True])
def test_unarchiving_date_is_saved_only_after_success_for_all_storages(
    storage_type: OutputStorageType, success: bool
) -> None:
    storage = Mock(spec=IOutputStorage, storage_type=storage_type)
    storage.output_exists.return_value = True
    storage.is_output_archived.return_value = True
    if not success:
        storage.unarchive_study_output.side_effect = RuntimeError("Unarchiving failed")
    repository = Mock()
    service = OutputService(
        matrix_service=Mock(),
        file_transfer_manager=Mock(),
        tmp_dir=Mock(),
        studies_repository=Mock(spec=IStudyMetadataProvider),
        storages=[storage],
        task_service=SimpleSyncTaskService(),
        output_repository=repository,
    )

    if success:
        before = current_time()
        service.unarchive_output("study", "output")
        repository.save_unarchiving_date.assert_called_once_with("study", "output", ANY)
        assert before <= repository.save_unarchiving_date.call_args.args[2] <= current_time()
    else:
        with pytest.raises(RuntimeError, match="Unarchiving failed"):
            service.unarchive_output("study", "output")
        repository.save_unarchiving_date.assert_not_called()
    repository.delete.assert_not_called()


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
    output_repository = Mock()
    file_outputs_provider = _file_outputs_provider(study_mock)
    output_storage = InStudyFileOutputStorage(
        cache=cache_mock,
        config=Mock(),
        outputs_provider=file_outputs_provider,
        remote_executor=Mock(),
        repository=Mock(),
    )

    studies_metadata_repository = _studies_repository(study_mock)
    output_service = OutputService(
        matrix_service=Mock(),
        file_transfer_manager=Mock(),
        tmp_dir=tmp_path,
        studies_repository=studies_metadata_repository,
        storages=[output_storage],
        task_service=task_service,
        output_repository=output_repository,
    )

    output_zipped = "some-output_zipped"
    output_unzipped = "20200101-0000eco"
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

    task_service.list_tasks.side_effect = None
    task_service.list_tasks.return_value = []
    cutoff = current_time()
    recent_unarchiving = cutoff + timedelta(seconds=1)
    # A successful unarchiving before task execution cancels automatic archiving.
    output_service.archive_output(study_id, output_unzipped, archive_before=cutoff)
    output_repository.get.side_effect = [Mock(last_unarchiving_date=recent_unarchiving)]
    task_service.add_task.call_args.args[0](Mock())
    assert (tmp_path / "output" / output_unzipped).is_dir()
    assert not (tmp_path / "output" / f"{output_unzipped}.zip").exists()
    assert not list((tmp_path / "output").glob("~archive-*.tmp"))
    output_repository.invalidate_disk_usage.assert_not_called()

    # Maintenance must also leave outputs alone while their whole study is being archived.
    task_service.list_tasks.return_value = [
        TaskDTO(
            id="study-archive",
            name=f"Study {study_name} archiving",
            status=TaskStatus.RUNNING,
            creation_date_utc=str(current_time()),
            type=TaskType.ARCHIVE,
            ref_id=study_id,
        )
    ]
    with pytest.raises(TaskAlreadyRunning):
        output_service.archive_output(study_id, output_unzipped, archive_before=cutoff)

    # Archive an output that remains eligible.
    task_service.list_tasks.return_value = []
    output_repository.get.side_effect = None
    output_repository.get.return_value = Mock(last_unarchiving_date=cutoff)
    output_service.archive_output(study_id, output_unzipped, archive_before=cutoff)
    task_service.add_task.call_args.args[0](Mock())
    assert not (tmp_path / "output" / output_unzipped).exists()
    assert (tmp_path / "output" / f"{output_unzipped}.zip").is_file()
    assert not list((tmp_path / "output").glob("~archive-*.tmp"))
    output_repository.invalidate_disk_usage.assert_called_once_with(study_id, output_unzipped)


def test_already_existing_study_raises_error_and_deletes_output() -> None:
    # TODO: remove or at least adapt this test when pre-check of the output id is implemented

    # Storage 1 will say that the output already exists
    storage1 = Mock(spec=IOutputStorage)
    storage1.storage_type = OutputStorageType.IN_STUDY_FILE_TREE
    storage1.output_exists.return_value = True

    # Storage 2 will receive the new output, but it will be deleted afterwards
    storage2 = Mock(spec=IOutputStorage)
    storage2.storage_type = OutputStorageType.V2
    storage2.import_output.return_value = "output_id"

    studies_repo = Mock(spec=IStudyMetadataProvider, unsafe=True)
    studies_repo.get_study_metadata.return_value = StudyMetadata("id", "name", StorageMode.FILESYSTEM)

    output_service = OutputService(
        storages=[storage1, storage2],
        matrix_service=Mock(),
        file_transfer_manager=Mock(),
        tmp_dir=Mock(),
        studies_repository=studies_repo,
        task_service=Mock(),
        output_repository=Mock(),
    )

    # Output
    with pytest.raises(OutputAlreadyExists):
        output_service.import_output("id", BytesIO(), storage_type=OutputStorageType.V2)

    storage1.import_output.assert_not_called()

    storage2.import_output.assert_called()
    storage2.delete_output.assert_called_with("id", "output_id")


@pytest.mark.parametrize(
    "output_id, unarchiving_date, eligible",
    [
        ("20251001-1200eco", None, True),
        ("20260102-1200eco", None, False),
        ("20260101-0000eco", None, True),
        ("20251001-1200eco", datetime(2026, 1, 2), False),
        ("20251001-1200eco", datetime(2025, 12, 31), True),
        ("20260102-1200eco", datetime(2025, 12, 31), True),
        ("20260102-1200eco", datetime(2026, 1, 1), True),
        ("invalid", datetime(2025, 12, 31), True),
        ("invalid", datetime(2026, 1, 2), False),
        ("invalid", None, False),
        ("20261301-1200eco", None, False),
    ],
)
def test_select_outputs_by_id_and_unarchiving_date(
    output_id: str, unarchiving_date: datetime | None, eligible: bool
) -> None:
    repository = Mock()
    repository.get_all.return_value = [
        Output(study_id="study", output_id=output_id, last_unarchiving_date=unarchiving_date),
        Output(study_id="study", output_id="other-output", last_unarchiving_date=datetime(2020, 1, 1)),
    ]
    storage = Mock(storage_type=OutputStorageType.IN_STUDY_FILE_TREE)
    storage.list_outputs.return_value = [
        OutputMetadata(output_id, in_study=True, archived=False),
        OutputMetadata("20200101-0000eco", in_study=True, archived=True),
    ]
    parquet_storage = Mock(storage_type=OutputStorageType.V2)
    service = OutputService(
        matrix_service=Mock(),
        file_transfer_manager=Mock(),
        tmp_dir=Mock(),
        studies_repository=Mock(),
        storages=[storage, parquet_storage],
        task_service=Mock(),
        output_repository=repository,
    )

    assert service.get_outputs_to_archive("study", datetime(2026, 1, 1)) == ([output_id] if eligible else [])
    parquet_storage.list_outputs.assert_not_called()
    repository.get_all.assert_called_once_with("study")
    repository.get.assert_not_called()
    repository.save_unarchiving_date.assert_not_called()
