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
import uuid
from pathlib import Path
from unittest.mock import ANY, Mock

import numpy as np
import pandas as pd
import pytest
from antares.study.version import StudyVersion

from antarest.core.config import DEFAULT_WORKSPACE_NAME, Config, StorageConfig, WorkspaceConfig
from antarest.core.exceptions import TaskAlreadyRunning
from antarest.core.filetransfer.model import FileDownload, FileDownloadTaskDTO
from antarest.core.model import PublicMode, StudyPermissionType
from antarest.core.remote.remote_executor import IRemoteExecutor
from antarest.core.tasks.model import TaskDTO, TaskResult, TaskStatus, TaskType
from antarest.core.tasks.service import ITaskService
from antarest.core.utils.utils import current_time
from antarest.login.model import User
from antarest.service_creator import build_output_service
from antarest.study.business.model.district_model import District
from antarest.study.directory_service import DirectoryService
from antarest.study.model import (
    ExportFormat,
    MatrixAggregationResultDTO,
    MatrixIndex,
    RawStudy,
    Study,
    StudyContentStatus,
    StudyDownloadDTO,
    StudyDownloadLevelDTO,
    StudyDownloadType,
    TimeSerie,
    TimeSeriesData,
)
from antarest.study.output.file_output_storage import FileOutputStorage, FileStudyOutputs, IFileOutputsProvider
from antarest.study.output.output_service import IStudyMetadataProvider, OutputService, StudyMetadata
from antarest.study.repository import StudyMetadataRepository
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    AreaConfig,
    FileStudyTreeConfig,
    LinkConfig,
    Mode,
    Simulation,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.matrix.output_series_matrix import OutputSeriesMatrix
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import FileStudyTree
from antarest.study.storage.utils import is_output_archived
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from antarest.worker.archive_worker import ArchiveTaskArgs
from tests.helpers import create_raw_study, with_admin_user
from tests.storage.conftest import SimpleSyncTaskService
from tests.storage.test_service import build_study_service, fill_study_service_with_command_context, with_jwt_user


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
        cache=cache_mock, outputs_provider=file_outputs_provider, remote_executor=remote_executor
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
    output_storage = FileOutputStorage(cache=cache_mock, outputs_provider=file_outputs_provider, remote_executor=Mock())

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


@with_jwt_user
def test_download_output(tmp_path: Path, command_context: CommandContext) -> None:
    study_service = Mock()
    repository = Mock(spec=StudyMetadataRepository)

    study_version = 870
    input_study = create_raw_study(
        id="c",
        path="c",
        name="c",
        version=str(study_version),
        content_status=StudyContentStatus.WARNING,
        workspace=DEFAULT_WORKSPACE_NAME,
        owner=User(id=0),
    )
    input_data = StudyDownloadDTO(
        type="AREA",
        years=[],
        level="annual",
        filterIn="",
        filterOut="",
        filter=[],
        columns=[],
        synthesis=False,
        includeClusters=True,
    )

    area = AreaConfig(
        name="area",
        links={"west": LinkConfig(filters_synthesis=[], filters_year=[])},
        thermals=[],
        renewables=[],
        filters_synthesis=[],
        filters_year=[],
    )

    sim = Simulation(
        name="",
        date="",
        mode=Mode.ECONOMY,
        nbyears=1,
        synthesis=True,
        by_year=True,
        error=False,
        playlist=[0],
        xpansion="",
    )
    file_study_tree_config = FileStudyTreeConfig(
        study_path=Path(input_study.path),
        path=Path(input_study.path),
        study_id=str(uuid.uuid4()),
        version=StudyVersion.parse(input_study.version),
        areas={"east": area},
        districts={"north": District(id="north", name="north")},
        outputs={"output-id": sim},
        store_new_set=False,
    )
    file_study_tree = Mock(spec=FileStudyTree, config=file_study_tree_config)

    repository.get.return_value = input_study
    config = Config(storage=StorageConfig(workspaces={DEFAULT_WORKSPACE_NAME: WorkspaceConfig()}))
    service = build_study_service(study_service, Mock(spec=DirectoryService), repository, config)
    fill_study_service_with_command_context(service, command_context)
    output_service = build_output_service(
        app_ctxt=None,
        study_service=service,
        task_service=service.task_service,
        filetransfer_service=service.file_transfer_manager,
        event_bus=service.event_bus,
        cache=service.cache_service,
        config=config,
        matrix_service=Mock(),
    )

    study_service.get_raw.return_value = FileStudy(config=file_study_tree_config, tree=file_study_tree)
    output_config = {
        "general": {
            "first-month-in-year": "january",
            "january.1st": "Monday",
            "leapyear": False,
            "first.weekday": "Monday",
            "simulation.start": 1,
            "simulation.end": 354,
        }
    }
    file_study_tree.get.side_effect = [
        output_config,
        output_config,
        output_config,
    ]

    res_study = Mock(spec=OutputSeriesMatrix)
    res_study.parse_dataframe.return_value = pd.DataFrame(columns=[("H. VAL", "Euro/MWh")], data=[[0.5]])
    res_study_details = Mock(spec=OutputSeriesMatrix)
    res_study_details.parse_dataframe.return_value = pd.DataFrame(columns=[("some cluster", "Euro/MWh")], data=[[0.8]])

    file_study_tree.get_node.side_effect = [
        res_study,
        res_study_details,
        res_study,
        res_study,
        res_study_details,
    ]

    # AREA TYPE
    res_matrix = MatrixAggregationResultDTO(
        index=MatrixIndex(
            start_date="2018-01-01 00:00:00",
            steps=1,
            first_week_size=7,
            level=StudyDownloadLevelDTO.ANNUAL,
        ),
        data=[
            TimeSeriesData(
                name="east",
                type=StudyDownloadType.AREA,
                data={
                    "1": [
                        TimeSerie(name="H. VAL", unit="Euro/MWh", data=np.array([0.5])),
                        TimeSerie(name="some cluster", unit="Euro/MWh", data=np.array([0.8])),
                    ]
                },
            )
        ],
        warnings=[],
    )

    tmp_file_path = tmp_path / "tmp.json"
    output_service.create_output_download(
        "study-id", "output-id", input_data, filetype=ExportFormat.JSON, tmp_export_file=tmp_file_path
    )
    assert MatrixAggregationResultDTO.model_validate_json(tmp_file_path.read_text()) == res_matrix
    # Ensures it was called with economy in lower case
    file_study_tree.get_node.assert_called_with(
        ["output", "output-id", "economy", "mc-ind", "00001", "areas", "east", "details-annual"]
    )

    # AREA TYPE - ZIP & TASK
    export_file_download = FileDownload(
        id="download-id",
        filename="filename",
        name="name",
        ready=False,
        path="path",
        expiration_date=current_time(),
    )
    service.file_transfer_manager.request_download.return_value = export_file_download  # type: ignore
    task_id = "task-id"
    service.task_service.add_task.return_value = task_id  # type: ignore

    result = output_service.start_output_download_creation(
        "study-id", "output-id", input_data, filetype=ExportFormat.ZIP
    )

    res_file_download = FileDownloadTaskDTO(file=export_file_download.to_dto(), task=task_id)
    assert result == res_file_download

    # LINK TYPE
    input_data.type = StudyDownloadType.LINK
    input_data.filter = ["east>west"]
    res_matrix = MatrixAggregationResultDTO(
        index=MatrixIndex(
            start_date="2018-01-01 00:00:00",
            steps=1,
            first_week_size=7,
            level=StudyDownloadLevelDTO.ANNUAL,
        ),
        data=[
            TimeSeriesData(
                name="east^west",
                type=StudyDownloadType.LINK,
                data={"1": [TimeSerie(name="H. VAL", unit="Euro/MWh", data=np.array([0.5]))]},
            )
        ],
        warnings=[],
    )
    tmp_file = tmp_path / "tmp.json"
    output_service.create_output_download(
        "study-id",
        "output-id",
        input_data,
        filetype=ExportFormat.JSON,
        tmp_export_file=tmp_file,
    )
    assert MatrixAggregationResultDTO.model_validate_json(tmp_file.read_text()) == res_matrix

    # CLUSTER TYPE
    input_data.type = StudyDownloadType.DISTRICT
    input_data.filter = []
    input_data.filterIn = "n"
    res_matrix = MatrixAggregationResultDTO(
        index=MatrixIndex(
            start_date="2018-01-01 00:00:00",
            steps=1,
            first_week_size=7,
            level=StudyDownloadLevelDTO.ANNUAL,
        ),
        data=[
            TimeSeriesData(
                name="north",
                type=StudyDownloadType.DISTRICT,
                data={
                    "1": [
                        TimeSerie(name="H. VAL", unit="Euro/MWh", data=np.array([0.5])),
                        TimeSerie(name="some cluster", unit="Euro/MWh", data=np.array([0.8])),
                    ]
                },
            )
        ],
        warnings=[],
    )
    tmp_file = tmp_path / "tmp.json"
    output_service.create_output_download(
        "study-id",
        "output-id",
        input_data,
        filetype=ExportFormat.JSON,
        tmp_export_file=tmp_file,
    )
    assert MatrixAggregationResultDTO.model_validate_json(tmp_file.read_text()) == res_matrix
