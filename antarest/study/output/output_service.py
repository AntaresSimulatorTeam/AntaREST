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
import itertools
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO, Callable, Iterable, Optional, Sequence

import pandas as pd
from fastapi import HTTPException
from starlette.responses import FileResponse

from antarest.core.exceptions import (
    OutputAlreadyArchived,
    OutputAlreadyUnarchived,
    OutputNotFound,
    TaskAlreadyRunning,
)
from antarest.core.filetransfer.model import FileDownloadTaskDTO
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.interfaces.cache import ICache
from antarest.core.model import StudyPermissionType
from antarest.core.serde.matrix_export import TableExportFormat
from antarest.core.serde.parquet_writer import (
    yield_dataframes_from_parquet,
)
from antarest.core.tasks.model import TaskListFilter, TaskResult, TaskStatus, TaskType
from antarest.core.tasks.service import ITaskNotifier, ITaskService
from antarest.core.utils.archives import ArchiveFormat
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.files import temp_file_path
from antarest.core.utils.utils import StopWatch, current_time
from antarest.login.utils import get_user_id
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.model import (
    MatrixAggregationResultDTO,
    MatrixFrequency,
    MatrixIndex,
    StudyDownloadDTO,
    StudyDownloadType,
    StudySimResultDTO,
)
from antarest.study.output.aggregator_management import (
    AREA_COL,
    CLUSTER_ID_COL,
    LINK_COL,
)
from antarest.study.output.output_model import (
    OutputVariables,
    OutputVariablesInformation,
    OutputVariablesList,
    OutputVariablesViewResponse,
    OutputVariablesViewStatus,
)
from antarest.study.output.storage.output_storage import BasicOutputMetadata, IOutputStorage, OutputStorageType
from antarest.study.output.utils import (
    MCYEAR_COL,
    MCAllAreasQueryFile,
    MCAllLinksQueryFile,
    MCIndAreasQueryFile,
    MCIndLinksQueryFile,
    QueryFileType,
    split_concatenated_columns_from_dataframe,
)
from antarest.study.output.variables_management import (
    OutputItemId,
    check_output_variable_exists,
    create_output_view_db_model,
    get_ids_for_aggregation,
    get_output_view_inside_db,
    get_query_file,
)
from antarest.study.output.variables_matrix_usage_provider import OutputVariablesMatrixUsageProvider
from antarest.study.storage.df_download import export_df_chunks
from antarest.study.storage.rawstudy.model.filesystem.config.model import Simulation
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.mcall.digest import (
    DigestUI,
)
from antarest.study.storage.utils import remove_from_cache

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class StudyMetadata:
    id: str
    name: str


class IStudyMetadataProvider(ABC):
    """
    Provides a lightweigth, read only, access to studies metadata.
    """

    @abstractmethod
    def get_study_metadata(self, study_id: str) -> StudyMetadata:
        pass

    @abstractmethod
    def assert_permission(self, study_id: str, permission: StudyPermissionType) -> None:
        """
        Check if the user has the given permission on the study

        Raises:
            UserHasNotPermissionError: if the user does not have the permission
            UnsupportedOperationOnArchivedStudy: if the study is archived
        """


class OutputVariablesViewMaterializationTask:
    """
    Task to materialize an output variables view
    """

    def __init__(
        self,
        study_id: str,
        output_id: str,
        output_service: "OutputService",
        variable_name: str,
        frequency: MatrixFrequency,
        output_identifier: OutputItemId,
    ) -> None:
        self._study_id = study_id
        self._output_id = output_id
        self._frequency = frequency
        self._variable_name = variable_name
        self._output_service = output_service
        self._output_identifier = output_identifier

    def _materialize_view(self) -> None:
        """Run the task"""
        with temp_file_path(dir=self._output_service._tmp_dir) as tmp_path:
            item_id, subitem_id = get_ids_for_aggregation(self._output_identifier)
            # Calls the aggregation with the right arguments
            task_id = self._output_service.start_aggregate_output_data(
                self._study_id,
                self._output_id,
                get_query_file(self._output_identifier),
                self._frequency,
                TableExportFormat.PARQUET,
                [self._variable_name],
                [item_id],
                tmp_path,
            )

            # Wait for the aggregation to end
            self._output_service._task_service.await_task(task_id)

            # Transform the dataframe to have the expected format
            if subitem_id:
                dataframe = pd.read_parquet(tmp_path, columns=[MCYEAR_COL, self._variable_name, CLUSTER_ID_COL])
                dataframe = dataframe[dataframe[CLUSTER_ID_COL] == subitem_id].drop(columns=[CLUSTER_ID_COL])
            else:
                dataframe = pd.read_parquet(tmp_path, columns=[MCYEAR_COL, self._variable_name])

        # Transform the dataframe to save only what's needed inside DB
        dataframe["idx"] = dataframe.groupby(MCYEAR_COL).cumcount()
        df_pivot = dataframe.pivot(index="idx", columns=MCYEAR_COL, values=self._variable_name)
        matrix_id = self._output_service._matrix_service.create(df_pivot)

        # Save the model inside DB
        db_model = create_output_view_db_model(
            self._study_id,
            self._output_id,
            self._variable_name,
            self._frequency,
            self._output_identifier,
            matrix_id,
        )
        db.session.add(db_model)
        db.session.commit()

    def run_task(self, notifier: ITaskNotifier) -> TaskResult:
        msg = f"Materializing output variables view for study '{self._study_id}' and output '{self._output_id}'"
        notifier.notify_message(msg)
        self._materialize_view()
        msg = f"Successfully materialized output variables view for study '{self._study_id}' and output '{self._output_id}'"
        notifier.notify_message(msg)
        return TaskResult(success=True, message=msg)

    # Make `OutputVariablesViewMaterializationTask` object callable
    __call__ = run_task


class OutputService:
    def __init__(
        self,
        storage: IOutputStorage | list[IOutputStorage],
        task_service: ITaskService,
        file_transfer_manager: FileTransferManager,
        matrix_service: ISimpleMatrixService,
        tmp_dir: Path,
        studies_repository: IStudyMetadataProvider,
        cache: ICache,
    ) -> None:
        self._storages = storage if isinstance(storage, list) else [storage]
        self._task_service = task_service
        self._file_transfer_manager = file_transfer_manager
        self._matrix_service = matrix_service
        self._tmp_dir = tmp_dir
        self._studies_repository = studies_repository
        self._cache = cache

        OutputVariablesMatrixUsageProvider(self._matrix_service)

    def _find_output_storage(self, study_id: str, output_id: str) -> IOutputStorage:
        for storage in self._storages:
            if storage.output_exists(study_id, output_id):
                return storage
        raise OutputNotFound(output_id)

    def _get_storage(self, storage_type: OutputStorageType | None) -> IOutputStorage:
        if not storage_type:
            return self._storages[0]
        for storage in self._storages:
            if storage.storage_type == storage_type:
                return storage
        raise ValueError(f"Output storage {storage_type} does not exist.")

    def get_digest_file(self, study_id: str, output_id: str) -> DigestUI:
        self._studies_repository.assert_permission(study_id, StudyPermissionType.READ)
        return self._find_output_storage(study_id, output_id).get_digest(study_id, output_id)

    def _get_ongoing_variables_view_materialization_task(
        self, item_identifier: OutputItemId, study_id: str, output_id: str, frequency: MatrixFrequency
    ) -> tuple[str | None, str]:
        item_id, subitem_id = get_ids_for_aggregation(item_identifier)
        task_name = f"Materializing output view for study `{study_id}`, output `{output_id}`, frequency `{frequency}`, id `{item_id}`"
        if subitem_id:
            task_name += f" sub_id `{subitem_id}`"

        study_tasks = self._task_service.list_tasks(
            TaskListFilter(
                ref_id=study_id,
                type=[TaskType.OUTPUT_VARIABLES_VIEW_MATERIALIZATION],
                status=[TaskStatus.RUNNING, TaskStatus.PENDING],
                name=task_name,
            )
        )
        if len(study_tasks) > 0:
            return study_tasks[0].id, task_name
        return None, task_name

    @staticmethod
    def _get_output_archive_task_names(study_id: str, study_name: str, output_id: str) -> tuple[str, str]:
        # TODO: why that inconsistency in naming, between the 2 types of tasks ?
        #       Locking would better not be implemented based on the task name, but in a more structured way.
        return (
            f"Archive output {study_id}/{output_id}",
            f"Unarchive output {study_name}/{output_id} ({study_id})",
        )

    def unarchive_output(self, study_id: str, output_id: str) -> Optional[str]:
        self._studies_repository.assert_permission(study_id, StudyPermissionType.READ)
        metadata = self._studies_repository.get_study_metadata(study_id)

        storage = self._find_output_storage(study_id, output_id)
        if not storage.is_output_archived(study_id, output_id):
            raise OutputAlreadyUnarchived(output_id)

        archive_task_names = OutputService._get_output_archive_task_names(metadata.id, metadata.name, output_id)
        task_name = archive_task_names[1]

        study_tasks = self._task_service.list_tasks(
            TaskListFilter(
                ref_id=study_id,
                type=[TaskType.UNARCHIVE, TaskType.ARCHIVE],
                status=[TaskStatus.RUNNING, TaskStatus.PENDING],
            )
        )
        if len(list(filter(lambda t: t.name in archive_task_names, study_tasks))):
            raise TaskAlreadyRunning()

        def unarchive_output_task(notifier: ITaskNotifier) -> TaskResult:
            try:
                stopwatch = StopWatch()
                self._find_output_storage(study_id, output_id).unarchive_study_output(study_id, output_id)
                remove_from_cache(cache=self._cache, root_id=study_id)
                stopwatch.log_elapsed(
                    lambda x: logger.info(f"Output {output_id} of study {study_id} unarchived in {x}s")
                )
                return TaskResult(
                    success=True,
                    message=f"Study output {study_id}/{output_id} successfully unarchived",
                )
            except Exception as e:
                logger.warning(
                    f"Could not unarchive the output {study_id}/{output_id}",
                    exc_info=e,
                )
                raise e

        task_id = self._task_service.add_task(
            unarchive_output_task,
            task_name,
            task_type=TaskType.UNARCHIVE,
            ref_id=study_id,
            progress=None,
            custom_event_messages=None,
        )

        return task_id

    def get_study_sim_result(self, study_id: str) -> list[StudySimResultDTO]:
        """
        Get global result information
        Args:
            study_id: study Id

        Returns: an object containing all needed information

        """
        self._studies_repository.assert_permission(study_id, StudyPermissionType.READ)
        logger.info(
            "study %s output listing asked by user %s",
            study_id,
            get_user_id(),
        )

        return [r for s in self._storages for r in s.get_study_sim_result(study_id)]

    def get_simulations(self, study_id: str) -> dict[str, Simulation]:
        """ """
        self._studies_repository.assert_permission(study_id, StudyPermissionType.READ)
        return {sim_id: sim for s in self._storages for sim_id, sim in s.get_simulations(study_id).items()}

    def import_output(
        self,
        uuid: str,
        output: BinaryIO | Path,
        output_name_suffix: Optional[str] = None,
        auto_unzip: bool = True,
        storage_type: OutputStorageType | None = None,
    ) -> Optional[str]:
        """
        Import specific output simulation inside study
        Args:
            uuid: study uuid
            output: zip file with simulation folder or simulation folder path
            output_name_suffix: optional suffix name for the output
            auto_unzip: add a task to unzip the output after import

        Returns: output simulation json formatted

        """
        logger.info(f"Importing new output for study {uuid}")
        self._studies_repository.assert_permission(uuid, StudyPermissionType.RUN)

        output_id = self._get_storage(storage_type).import_output(uuid, output, output_name_suffix)
        remove_from_cache(cache=self._cache, root_id=uuid)
        logger.info("output added to study %s by user %s", uuid, get_user_id())

        if output_id and isinstance(output, Path) and output.suffix == ArchiveFormat.ZIP and auto_unzip:
            self.unarchive_output(uuid, output_id)

        return output_id

    def get_output_time_index(self, study_id: str, output_id: str, frequency: MatrixFrequency) -> MatrixIndex:
        """
        Get the time index (start date and step count) for output matrices with a given frequency.
        Args:
            study_id: ID of the study
            output_id: ID of the output
            frequency: temporal frequency (hourly, daily, weekly, monthly, annually)
        Returns:
            MatrixIndex with start_date, steps, first_week_size and level
        """
        self._studies_repository.assert_permission(study_id, StudyPermissionType.READ)
        return self._find_output_storage(study_id, output_id).get_output_time_index(study_id, output_id, frequency)

    def export_output(self, study_uuid: str, output_uuid: str) -> FileDownloadTaskDTO:
        """
        Export study output to a zip file.
        Args:
            study_uuid: study id
            output_uuid: output id
        """
        self._studies_repository.assert_permission(study_uuid, StudyPermissionType.READ)
        metadata = self._studies_repository.get_study_metadata(study_uuid)

        logger.info(f"Exporting {output_uuid} from study {study_uuid}")
        export_name = f"Study output {metadata.name}/{output_uuid} export"
        export_file_download = self._file_transfer_manager.request_download(
            f"{metadata.name}-{study_uuid}-{output_uuid}{ArchiveFormat.ZIP}", export_name
        )
        export_path = Path(export_file_download.path)
        export_id = export_file_download.id

        def export_task(notifier: ITaskNotifier) -> TaskResult:
            try:
                self._find_output_storage(study_uuid, output_uuid).export_output(
                    study_id=study_uuid,
                    output_id=output_uuid,
                    target=export_path,
                )
                self._file_transfer_manager.set_ready(export_id)
                return TaskResult(
                    success=True,
                    message=f"Study output {metadata.name}/{output_uuid} successfully exported",
                )
            except Exception as e:
                self._file_transfer_manager.fail(export_id, str(e))
                raise e

        task_id = self._task_service.add_task(
            export_task,
            export_name,
            task_type=TaskType.EXPORT,
            ref_id=study_uuid,
            progress=None,
            custom_event_messages=None,
        )

        return FileDownloadTaskDTO(file=export_file_download.to_dto(), task=task_id)

    def download_outputs(self, study_id: str, output_id: str, data: StudyDownloadDTO, tmp_file: Path) -> FileResponse:
        """
        Download outputs
        Args:
            study_id: study ID.
            output_id: output ID.
            data: Json parameters.

        Returns: FileResponse containing the asked data.

        """
        self._studies_repository.assert_permission(study_id, StudyPermissionType.READ)
        logger.info(f"Study {study_id} output download asked by {get_user_id()}")

        # Fetches time_index
        time_index = self.get_output_time_index(study_id, output_id, data.level)

        # Fetches the data
        query_files: list[QueryFileType]
        if data.type == StudyDownloadType.LINK:
            query_files = [MCIndLinksQueryFile.VALUES]
        else:
            query_files = [MCIndAreasQueryFile.VALUES]
            if data.include_clusters:
                query_files.append(MCIndAreasQueryFile.DETAILS)
                query_files.append(MCIndAreasQueryFile.DETAILS_RES)

        file_paths = []
        try:
            # Launch all aggregation tasks
            for query_file in query_files:
                file_name = str(uuid.uuid4())
                file_path = self._tmp_dir / file_name
                task_id = self.start_aggregate_output_data(
                    study_id,
                    output_id,
                    query_file,
                    MatrixFrequency(data.level.value),
                    TableExportFormat.PARQUET,
                    data.columns,
                    data.filter,
                    file_path,
                    transform_columns_headers=False,
                    mc_years=data.years,
                )
                # Wait for the aggregation to end
                self._task_service.await_task(task_id)

                # Aggregation can fail (for instance, when asking renewables values and no cluster exists)
                # If so, we shouldn't raise to keep backward compatibility
                task = self._task_service.status_task(task_id)
                if task.status != TaskStatus.COMPLETED:
                    file_path.unlink(missing_ok=True)
                    continue

                file_paths.append(file_path)

            # Once they all ended, build the final response
            intermediary_dict: dict[str, Any] = {}
            # We're opening the parquet files chunk by chunk to avoid flooding memory
            for dataframe in yield_dataframes_from_parquet(file_paths, []):
                # Convert the dataframe in the right response
                column_type_name = LINK_COL if data.type == StudyDownloadType.LINK else AREA_COL
                for object_name, object_group in dataframe.groupby(column_type_name):
                    assert isinstance(object_name, str)
                    assert isinstance(object_group, pd.DataFrame)
                    element_name = object_name
                    if data.type == StudyDownloadType.LINK:
                        element_name = "^".join(element_name.split(" - "))

                    for year, year_group in object_group.groupby(MCYEAR_COL):
                        year_group.drop(columns=[column_type_name, MCYEAR_COL], inplace=True)
                        variables_list = list(split_concatenated_columns_from_dataframe(year_group))
                        intermediary_dict.setdefault(element_name, {}).setdefault(str(year), []).extend(variables_list)

            response = MatrixAggregationResultDTO.model_validate(
                {
                    "index": time_index,
                    "data": [
                        {"type": data.type, "name": name, "data": values} for name, values in intermediary_dict.items()
                    ],
                }
            )

            with open(tmp_file, "w", encoding="utf-8") as fh:
                fh.write(response.model_dump_json())

        finally:
            for file_path in file_paths:
                file_path.unlink(missing_ok=True)

        return FileResponse(tmp_file, headers={"Content-Disposition": "inline"}, media_type="application/json")

    def delete_output(self, uuid: str, output_name: str) -> None:
        """
        Delete specific output simulation in study
        Args:
            uuid: study uuid
            output_name: output simulation name

        Returns:

        """
        self._studies_repository.assert_permission(uuid, StudyPermissionType.WRITE)

        self._find_output_storage(uuid, output_name).delete_output(uuid, output_name)
        remove_from_cache(cache=self._cache, root_id=uuid)

        logger.info(f"Output {output_name} deleted from study {uuid}")

    def archive_outputs(self, study_id: str) -> list[str]:
        logger.info(f"Archiving all outputs for study {study_id}")
        self._studies_repository.assert_permission(study_id, StudyPermissionType.WRITE)

        outputs = self.get_study_sim_result(study_id)
        task_ids = []
        for output in outputs:
            if not output.archived:
                task_id = self.archive_output(study_id, output.name)
                if task_id:
                    task_ids.append(task_id)
        return task_ids

    def archive_output(
        self,
        study_id: str,
        output_id: str,
        force: bool = False,
    ) -> Optional[str]:
        self._studies_repository.assert_permission(study_id, StudyPermissionType.WRITE)
        metadata = self._studies_repository.get_study_metadata(study_id)

        storage = self._find_output_storage(study_id, output_id)
        if storage.is_output_archived(study_id, output_id):
            raise OutputAlreadyArchived(output_id)

        archive_task_names = self._get_output_archive_task_names(metadata.id, metadata.name, output_id)
        task_name = archive_task_names[0]

        if not force:
            study_tasks = self._task_service.list_tasks(
                TaskListFilter(
                    ref_id=study_id,
                    name=task_name,
                    type=[TaskType.UNARCHIVE, TaskType.ARCHIVE],
                    status=[TaskStatus.RUNNING, TaskStatus.PENDING],
                )
            )
            if len(list(filter(lambda t: t.name in archive_task_names, study_tasks))):
                raise TaskAlreadyRunning()

        def archive_output_task(notifier: ITaskNotifier) -> TaskResult:
            try:
                stopwatch = StopWatch()
                storage.archive_study_output(study_id, output_id)
                remove_from_cache(cache=self._cache, root_id=study_id)
                stopwatch.log_elapsed(lambda x: logger.info(f"Output {output_id} of study {study_id} archived in {x}s"))
                return TaskResult(
                    success=True,
                    message=f"Study output {study_id}/{output_id} successfully archived",
                )
            except Exception as e:
                logger.warning(
                    f"Could not archive the output {study_id}/{output_id}",
                    exc_info=e,
                )
                raise e

        task_id = self._task_service.add_task(
            archive_output_task,
            task_name,
            task_type=TaskType.ARCHIVE,
            ref_id=study_id,
            progress=None,
            custom_event_messages=None,
        )

        return task_id

    def create_aggregated_output_data_download(
        self,
        uuid: str,
        output_id: str,
        query_file: MCIndAreasQueryFile | MCAllAreasQueryFile | MCIndLinksQueryFile | MCAllLinksQueryFile,
        frequency: MatrixFrequency,
        export_format: TableExportFormat,
        columns_names: Sequence[str],
        ids_to_consider: Sequence[str],
        download_name: str,
        download_log: str,
        download_expiration_time_in_minutes: int,
        mc_years: Optional[Sequence[int]] = None,
    ) -> str:
        """
        Creates a download, and starts the task to fill it with aggregated output data.

        Returns:
            the ID of the download, which will be filled with output data.
        """
        self._studies_repository.assert_permission(uuid, StudyPermissionType.READ)
        study_name = self._studies_repository.get_study_metadata(uuid).name
        logger.info(download_log)
        file_download = self._file_transfer_manager.request_download(
            f"{study_name}-{uuid}-{output_id}{export_format.suffix}",
            download_name,
            expiration_time_in_minutes=download_expiration_time_in_minutes,
        )
        file_download_path = Path(file_download.path)
        download_id: str = file_download.id

        self.start_aggregate_output_data(
            uuid,
            output_id,
            query_file,
            frequency,
            export_format,
            columns_names,
            ids_to_consider,
            file_download_path,
            mc_years=mc_years,
            on_success=lambda: self._file_transfer_manager.set_ready(download_id, use_notification=False),
            on_failure=lambda e: self._file_transfer_manager.fail(download_id, str(e)),
        )

        return download_id

    def start_aggregate_output_data(
        self,
        uuid: str,
        output_id: str,
        query_file: MCIndAreasQueryFile | MCAllAreasQueryFile | MCIndLinksQueryFile | MCAllLinksQueryFile,
        frequency: MatrixFrequency,
        export_format: TableExportFormat,
        columns_names: Sequence[str],
        ids_to_consider: Sequence[str],
        file_path: Path,
        transform_columns_headers: bool = True,
        mc_years: Optional[Sequence[int]] = None,
        on_success: Optional[Callable[[], None]] = None,
        on_failure: Optional[Callable[[Exception], None]] = None,
    ) -> str:
        """
        Starts a task aggregating output data based on several filtering conditions.

        Args:
            uuid: study uuid
            output_id: simulation output ID
            query_file: which types of data to retrieve: "values", "details", "details-st-storage", "details-res", "ids"
            frequency: yearly, monthly, weekly, daily or hourly.
            export_format: format of the export file
            columns_names: regexes (if details) or columns to be selected, if empty, all columns are selected
            ids_to_consider: list of areas or links ids to consider, if empty, all areas are selected
            file_path: path of the file where output aggregation data will be stored
            transform_columns_headers: If False, keeps the output columns as written by the Simulator
            mc_years: list of monte-carlo years, if empty, all years are selected (only for mc-ind)
            on_success: callback to be called when the task is completed successfully
            on_failure: callback to be called when the task fails with an exception

        Returns:
            Aggregation task id
        """
        self._studies_repository.assert_permission(uuid, StudyPermissionType.READ)

        def aggregate_output_task(notifier: ITaskNotifier) -> TaskResult:
            try:
                stopwatch = StopWatch()
                stopwatch.log_elapsed(
                    lambda x: logger.info(f"Launch aggregation step for output '{output_id}' of study '{uuid}'.")
                )

                results = self._find_output_storage(uuid, output_id).aggregate_output_data(
                    uuid,
                    output_id,
                    query_file,
                    frequency,
                    ids_to_consider,
                    columns_names,
                    transform_columns_headers,
                    mc_years,
                )
                export_df_chunks(self._tmp_dir, file_path, results, export_format)

                stopwatch.log_elapsed(lambda x: logger.info(f"Store aggregation outputs in '{file_path}'."))

                if on_success:
                    on_success()

                stopwatch.log_elapsed(
                    lambda x: logger.info(f"Aggregated output file '{file_path}' is ready for download.")
                )
                return TaskResult(
                    success=True,
                    message=f"Successfully aggregated output data for study '{uuid}'."
                    f" Results are stored in '{file_path}'.",
                )

            except Exception as e:
                if on_failure:
                    on_failure(e)
                raise e

        task_id = self._task_service.add_task(
            aggregate_output_task,
            f"Aggregate output {output_id} of study {uuid}.",
            task_type=TaskType.OUTPUT_AGGREGATION,
            ref_id=uuid,
            progress=None,
            custom_event_messages=None,
        )

        return task_id

    def get_output_variables_list(self, study_id: str, output_id: str) -> OutputVariablesList:
        """
        Returns the list of variables concerning a given output.
        First, try to fetch the given data inside DB.
        If present, return the data.
        If not, parse the output headers to build the object. Before returning it, save it inside DB for next calls.
        """
        self._studies_repository.assert_permission(study_id, StudyPermissionType.READ)

        output_variables: OutputVariables | None = db.session.get(OutputVariables, (study_id, output_id))
        if output_variables:
            return output_variables.to_model()

        # Fetches the data from stored output
        model = self._find_output_storage(study_id, output_id).extract_variables_list(study_id, output_id)

        # Save the model inside DB for next calls
        db_model = OutputVariables.from_model(study_id, output_id, model)
        db.session.add(db_model)
        db.session.commit()

        # Returns it
        return model

    def get_output_variables_information(self, study_id: str, output_id: str) -> OutputVariablesInformation:
        """
        Endpoint used by ImaGrid
        """
        self._studies_repository.assert_permission(study_id, StudyPermissionType.READ)

        variables_list = self.get_output_variables_list(study_id, output_id)
        return OutputVariablesInformation.from_variables_list(variables_list)

    def get_output_variables_view(
        self,
        study_id: str,
        output_id: str,
        output_item_id: OutputItemId,
        variable_name: str,
        frequency: MatrixFrequency,
    ) -> pd.DataFrame | OutputVariablesViewResponse:
        """
        If the view is already registered in DB, updates its `last_read` value and returns it.
        Else, returns a pydantic model specifying if the view materialization is in progress or not.
        """
        self._studies_repository.assert_permission(study_id, StudyPermissionType.READ)

        db_model = get_output_view_inside_db(study_id, output_id, variable_name, frequency, output_item_id)
        if db_model is not None:
            # Update `last_read` value inside DB
            db_model.last_read = current_time()
            db.session.merge(db_model)
            db.session.commit()

            # Return the dataframe
            return self._matrix_service.get(db_model.matrix_id)

        # Checks if the asked couple `variable name` / `output_identifier` exists for the output
        available_variables = self.get_output_variables_list(study_id, output_id)
        check_output_variable_exists(output_id, variable_name, available_variables, output_item_id)

        # Return a 404 Response with a body specifying if the materialization is in progress or not.
        task_id, _ = self._get_ongoing_variables_view_materialization_task(
            output_item_id, study_id, output_id, frequency
        )
        status = OutputVariablesViewStatus.IN_PROGRESS if task_id else OutputVariablesViewStatus.NOT_FOUND
        return OutputVariablesViewResponse(status=status, task_id=task_id)

    def materialize_output_variables_view(
        self,
        study_id: str,
        output_id: str,
        output_item_id: OutputItemId,
        variable_name: str,
        frequency: MatrixFrequency,
    ) -> str:
        """
        If the view is already registered in DB, raise an HTTP Conflict error.
        Else, launch a task that fetches the required data and stores it inside the database.
        """
        self._studies_repository.assert_permission(study_id, StudyPermissionType.READ)

        db_model = get_output_view_inside_db(study_id, output_id, variable_name, frequency, output_item_id)
        if db_model is not None:
            raise HTTPException(status_code=417, detail="The output variables view is already materialized in DB")

        # If a task materializing the same view is already running, returns its id
        task_id, task_name = self._get_ongoing_variables_view_materialization_task(
            output_item_id, study_id, output_id, frequency
        )
        if task_id:
            return task_id

        # Checks the asked couple `variable name` / `object_id` exists for the output
        available_variables = self.get_output_variables_list(study_id, output_id)
        check_output_variable_exists(output_id, variable_name, available_variables, output_item_id)

        # Materialize the view
        task = OutputVariablesViewMaterializationTask(
            study_id, output_id, self, variable_name, frequency, output_item_id
        )

        return self._task_service.add_task(
            task,
            task_name,
            task_type=TaskType.OUTPUT_VARIABLES_VIEW_MATERIALIZATION,
            ref_id=study_id,
            progress=0,
            custom_event_messages=None,
        )

    def copy_output(self, src_study_id: str, target_study_id: str, output_name: str) -> None:
        """
        Copies one output from src_study_id to target_study_id.
        """
        self._studies_repository.assert_permission(src_study_id, StudyPermissionType.READ)
        self._studies_repository.assert_permission(target_study_id, StudyPermissionType.WRITE)
        self._find_output_storage(src_study_id, output_name).copy_output(src_study_id, target_study_id, output_name)
        remove_from_cache(cache=self._cache, root_id=target_study_id)

    def write_output_to_dir(self, study_id: str, output_id: str, outputs_dir: Path) -> None:
        self._studies_repository.assert_permission(study_id, StudyPermissionType.READ)
        self._find_output_storage(study_id, output_id).write_output_to_dir(study_id, output_id, outputs_dir)

    def list_outputs(self, study_id: str) -> Iterable[BasicOutputMetadata]:
        return itertools.chain(*(s.list_outputs(study_id) for s in self._storages))
