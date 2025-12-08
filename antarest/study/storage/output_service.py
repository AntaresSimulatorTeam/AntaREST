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
import logging
from pathlib import Path
from typing import BinaryIO, Callable, Optional, Sequence

import pandas as pd
from fastapi import HTTPException
from starlette.responses import FileResponse, Response

from antarest.core.config import DEFAULT_WORKSPACE_NAME
from antarest.core.exceptions import (
    OutputAlreadyArchived,
    OutputAlreadyUnarchived,
    OutputNotFound,
    TaskAlreadyRunning,
)
from antarest.core.filetransfer.model import FileDownloadTaskDTO
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.interfaces.eventbus import Event, EventType, IEventBus
from antarest.core.model import PermissionInfo, StudyPermissionType
from antarest.core.serde.matrix_export import TableExportFormat
from antarest.core.tasks.model import TaskListFilter, TaskResult, TaskStatus, TaskType
from antarest.core.tasks.service import ITaskNotifier, ITaskService
from antarest.core.utils.archives import ArchiveFormat
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.files import temp_file_path
from antarest.core.utils.utils import StopWatch, current_time
from antarest.login.utils import get_user_id
from antarest.study.business.output.aggregator_management import CLUSTER_ID_COL, AggregatorManager
from antarest.study.business.output.utils import (
    MCYEAR_COL,
    MCAllAreasQueryFile,
    MCAllLinksQueryFile,
    MCIndAreasQueryFile,
    MCIndLinksQueryFile,
)
from antarest.study.business.output.variables_management import (
    OutputIdentifier,
    check_arguments_coherence_and_return_identifier,
    check_output_variable_exists,
    create_output_view_db_model,
    extract_variables_list,
    get_output_view_inside_db,
)
from antarest.study.business.output.variables_matrix_usage_provider import OutputVariablesMatrixUsageProvider
from antarest.study.model import (
    ExportFormat,
    MatrixIndex,
    Study,
    StudyDownloadDTO,
    StudyDownloadLevelDTO,
    StudySimResultDTO,
)
from antarest.study.service import StudyService
from antarest.study.storage.df_download import export_df_chunks
from antarest.study.storage.output_model import (
    OutputVariables,
    OutputVariablesInformation,
    OutputVariablesList,
    OutputVariablesType,
)
from antarest.study.storage.output_storage import IOutputStorage
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.mcall.digest import (
    DigestSynthesis,
    DigestUI,
)
from antarest.study.storage.study_download_utils import StudyDownloader
from antarest.study.storage.utils import assert_permission, get_start_date, is_output_archived, remove_from_cache
from antarest.worker.archive_worker import ArchiveTaskArgs

logger = logging.getLogger(__name__)


class OutputVariablesViewMaterializationTask:
    """
    Task to materialize an output variables view
    """

    def __init__(
        self,
        study_id: str,
        output_id: str,
        output_service: "OutputService",
        variable_type: OutputVariablesType,
        variable_name: str,
        frequency: MatrixFrequency,
        output_identifier: OutputIdentifier,
    ) -> None:
        self._study_id = study_id
        self._output_id = output_id
        self._variable_type = variable_type
        self._frequency = frequency
        self._variable_name = variable_name
        self._output_service = output_service
        self._output_identifier = output_identifier

    def _materialize_view(self) -> None:
        """Run the task"""
        with temp_file_path(dir=self._output_service._study_service.config.storage.tmp_dir) as tmp_path:
            # Calls the aggregation with the right arguments
            task_id = self._output_service.start_aggregate_output_data(
                self._study_id,
                self._output_id,
                self._output_identifier.query_file,
                self._frequency,
                TableExportFormat.PARQUET,
                [self._variable_name],
                [self._output_identifier.get_id_for_aggregation()],
                tmp_path,
            )

            # Wait for the aggregation to end
            self._output_service._task_service.await_task(task_id)

            # Transform the dataframe to have the expected format
            if cluster_id := self._output_identifier.get_sub_id_for_aggregation():
                dataframe = pd.read_parquet(tmp_path, columns=[MCYEAR_COL, self._variable_name, CLUSTER_ID_COL])
                dataframe = dataframe[dataframe[CLUSTER_ID_COL] == cluster_id].drop(columns=[CLUSTER_ID_COL])
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
            self._variable_type,
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
        study_service: StudyService,
        storage: IOutputStorage,
        task_service: ITaskService,
        file_transfer_manager: FileTransferManager,
        event_bus: IEventBus,
    ) -> None:
        self._study_service = study_service
        self._storage = storage
        self._task_service = task_service
        self._file_transfer_manager = file_transfer_manager
        self._event_bus = event_bus
        self._matrix_service = (
            self._study_service.storage_service.variant_study_service.command_factory.command_context.matrix_service
        )
        OutputVariablesMatrixUsageProvider(self._matrix_service)

    def get_digest_file(self, study_id: str, output_id: str) -> DigestUI:
        study = self._study_service.get_study(study_id)
        assert_permission(study, StudyPermissionType.READ)
        file_study = self._study_service.get_file_study(study)
        digest_node = file_study.tree.get_node(url=["output", output_id, "economy", "mc-all", "grid", "digest"])
        assert isinstance(digest_node, DigestSynthesis)
        return digest_node.get_ui()

    @staticmethod
    def _get_output_archive_task_names(study: Study, output_id: str) -> tuple[str, str]:
        return (
            f"Archive output {study.id}/{output_id}",
            f"Unarchive output {study.name}/{output_id} ({study.id})",
        )

    def unarchive_output(self, study_id: str, output_id: str) -> Optional[str]:
        study = self._study_service.get_study(study_id)
        assert_permission(study, StudyPermissionType.READ)
        self._study_service.assert_study_unarchived(study)

        output_path = Path(study.path) / "output" / output_id
        if not is_output_archived(output_path):
            if not output_path.exists():
                raise OutputNotFound(output_id)
            raise OutputAlreadyUnarchived(output_id)

        archive_task_names = OutputService._get_output_archive_task_names(study, output_id)
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
                study = self._study_service.get_study(study_id)
                stopwatch = StopWatch()
                self._storage.unarchive_study_output(study, output_id)
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

        task_id: Optional[str] = None
        workspace = getattr(study, "workspace", DEFAULT_WORKSPACE_NAME)
        if workspace != DEFAULT_WORKSPACE_NAME:
            dest = Path(study.path) / "output" / output_id
            src = Path(study.path) / "output" / f"{output_id}{ArchiveFormat.ZIP}"
            task_id = self._task_service.add_worker_task(
                TaskType.UNARCHIVE,
                f"unarchive_{workspace}",
                ArchiveTaskArgs(src=str(src), dest=str(dest)).model_dump(mode="json"),
                name=task_name,
                ref_id=study.id,
            )

        if not task_id:
            task_id = self._task_service.add_task(
                unarchive_output_task,
                task_name,
                task_type=TaskType.UNARCHIVE,
                ref_id=study.id,
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
        study = self._study_service.get_study(study_id)
        assert_permission(study, StudyPermissionType.READ)
        logger.info(
            "study %s output listing asked by user %s",
            study_id,
            get_user_id(),
        )

        return self._storage.get_study_sim_result(study)

    def import_output(
        self,
        uuid: str,
        output: BinaryIO | Path,
        output_name_suffix: Optional[str] = None,
        auto_unzip: bool = True,
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
        study = self._study_service.get_study(uuid)
        assert_permission(study, StudyPermissionType.RUN)
        self._study_service.assert_study_unarchived(study)

        output_id = self._storage.import_output(study, output, output_name_suffix)
        remove_from_cache(cache=self._study_service.cache_service, root_id=study.id)
        logger.info("output added to study %s by user %s", uuid, get_user_id())

        if output_id and isinstance(output, Path) and output.suffix == ArchiveFormat.ZIP and auto_unzip:
            self.unarchive_output(uuid, output_id)

        return output_id

    def get_output_time_index(self, study_id: str, output_id: str, frequency: StudyDownloadLevelDTO) -> MatrixIndex:
        """
        Get the time index (start date and step count) for output matrices with a given frequency.
        Args:
            study_id: ID of the study
            output_id: ID of the output
            frequency: temporal frequency (hourly, daily, weekly, monthly, annually)
        Returns:
            MatrixIndex with start_date, steps, first_week_size and level
        """
        study = self._study_service.get_study(study_id)
        assert_permission(study, StudyPermissionType.READ)
        file_study = self._study_service.get_file_study(study)
        return get_start_date(file_study, output_id, frequency)

    def export_output(self, study_uuid: str, output_uuid: str) -> FileDownloadTaskDTO:
        """
        Export study output to a zip file.
        Args:
            study_uuid: study id
            output_uuid: output id
        """
        study = self._study_service.get_study(study_uuid)
        assert_permission(study, StudyPermissionType.READ)
        self._study_service.assert_study_unarchived(study)

        logger.info(f"Exporting {output_uuid} from study {study_uuid}")
        export_name = f"Study output {study.name}/{output_uuid} export"
        export_file_download = self._file_transfer_manager.request_download(
            f"{study.name}-{study_uuid}-{output_uuid}{ArchiveFormat.ZIP}", export_name
        )
        export_path = Path(export_file_download.path)
        export_id = export_file_download.id

        def export_task(notifier: ITaskNotifier) -> TaskResult:
            try:
                target_study = self._study_service.get_study(study_uuid)
                self._storage.export_output(
                    metadata=target_study,
                    output_id=output_uuid,
                    target=export_path,
                )
                self._file_transfer_manager.set_ready(export_id)
                return TaskResult(
                    success=True,
                    message=f"Study output {study_uuid}/{output_uuid} successfully exported",
                )
            except Exception as e:
                self._file_transfer_manager.fail(export_id, str(e))
                raise e

        task_id = self._task_service.add_task(
            export_task,
            export_name,
            task_type=TaskType.EXPORT,
            ref_id=study.id,
            progress=None,
            custom_event_messages=None,
        )

        return FileDownloadTaskDTO(file=export_file_download.to_dto(), task=task_id)

    def download_outputs(
        self,
        study_id: str,
        output_id: str,
        data: StudyDownloadDTO,
        use_task: bool,
        filetype: ExportFormat,
        tmp_export_file: Optional[Path] = None,
    ) -> Response | FileDownloadTaskDTO | FileResponse:
        """
        Download outputs
        Args:
            study_id: study ID.
            output_id: output ID.
            data: Json parameters.
            use_task: use task or not.
            filetype: type of returning file,.
            tmp_export_file: temporary file (if `use_task` is false),.

        Returns: CSV content file

        """
        # GET STUDY ID
        study = self._study_service.get_study(study_id)
        assert_permission(study, StudyPermissionType.READ)
        self._study_service.assert_study_unarchived(study)
        logger.info(f"Study {study_id} output download asked by {get_user_id()}")

        if use_task:
            logger.info(f"Exporting {output_id} from study {study_id}")
            export_name = f"Study filtered output {study.name}/{output_id} export"
            export_file_download = self._file_transfer_manager.request_download(
                f"{study.name}-{study_id}-{output_id}_filtered{filetype.suffix}", export_name
            )
            export_path = Path(export_file_download.path)
            export_id = export_file_download.id

            def export_task(_notifier: ITaskNotifier) -> TaskResult:
                try:
                    _study = self._study_service.get_study(study_id)
                    _stopwatch = StopWatch()
                    _matrix = StudyDownloader.build(
                        self._study_service.get_file_study(_study),
                        output_id,
                        data,
                    )
                    _stopwatch.log_elapsed(
                        lambda x: logger.info(f"Study {study_id} filtered output {output_id} built in {x}s")
                    )
                    StudyDownloader.export(_matrix, filetype, export_path)
                    _stopwatch.log_elapsed(
                        lambda x: logger.info(f"Study {study_id} filtered output {output_id} exported in {x}s")
                    )
                    self._file_transfer_manager.set_ready(export_id)
                    return TaskResult(
                        success=True,
                        message=f"Study filtered output {study_id}/{output_id} successfully exported",
                    )
                except Exception as e:
                    self._file_transfer_manager.fail(export_id, str(e))
                    raise

            task_id = self._task_service.add_task(
                export_task,
                export_name,
                task_type=TaskType.EXPORT,
                ref_id=study.id,
                progress=None,
                custom_event_messages=None,
            )

            return FileDownloadTaskDTO(file=export_file_download.to_dto(), task=task_id)
        else:
            stopwatch = StopWatch()
            matrix = StudyDownloader.build(
                self._study_service.get_file_study(study),
                output_id,
                data,
            )
            stopwatch.log_elapsed(lambda x: logger.info(f"Study {study_id} filtered output {output_id} built in {x}s"))
            if tmp_export_file is not None:
                StudyDownloader.export(matrix, filetype, tmp_export_file)
                stopwatch.log_elapsed(
                    lambda x: logger.info(f"Study {study_id} filtered output {output_id} exported in {x}s")
                )

                if filetype == ExportFormat.JSON:
                    headers = {"Content-Disposition": "inline"}
                elif filetype == ExportFormat.TAR_GZ:
                    headers = {"Content-Disposition": f'attachment; filename="output-{output_id}.tar.gz'}
                elif filetype == ExportFormat.ZIP:
                    headers = {"Content-Disposition": f'attachment; filename="output-{output_id}.zip'}
                else:  # pragma: no cover
                    raise NotImplementedError(f"Export format {filetype} is not supported")

                return FileResponse(tmp_export_file, headers=headers, media_type=filetype)

            else:
                json_response = matrix.model_dump_json()
                return Response(content=json_response, media_type="application/json")

    def delete_output(self, uuid: str, output_name: str) -> None:
        """
        Delete specific output simulation in study
        Args:
            uuid: study uuid
            output_name: output simulation name

        Returns:

        """
        study = self._study_service.get_study(uuid)
        assert_permission(study, StudyPermissionType.WRITE)
        self._study_service.assert_study_unarchived(study)
        self._storage.delete_output(study, output_name)
        self._event_bus.push(
            Event(
                type=EventType.STUDY_DATA_EDITED,
                payload=study.to_json_summary(),
                permissions=PermissionInfo.from_study(study),
            )
        )

        logger.info(f"Output {output_name} deleted from study {uuid}")

    def archive_outputs(self, study_id: str) -> list[str]:
        logger.info(f"Archiving all outputs for study {study_id}")
        study = self._study_service.get_study(study_id)
        assert_permission(study, StudyPermissionType.WRITE)
        self._study_service.assert_study_unarchived(study)
        file_study = self._study_service.get_file_study(study)
        task_ids = []
        for output in file_study.config.outputs:
            if not file_study.config.outputs[output].archived:
                task_id = self.archive_output(study_id, output)
                if task_id:
                    task_ids.append(task_id)
        return task_ids

    def archive_output(
        self,
        study_id: str,
        output_id: str,
        force: bool = False,
    ) -> Optional[str]:
        study = self._study_service.get_study(study_id)
        assert_permission(study, StudyPermissionType.WRITE)
        self._study_service.assert_study_unarchived(study)

        output_path = Path(study.path) / "output" / output_id
        if is_output_archived(output_path):
            raise OutputAlreadyArchived(output_id)
        if not output_path.exists():
            raise OutputNotFound(output_id)

        archive_task_names = self._get_output_archive_task_names(study, output_id)
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
                study = self._study_service.get_study(study_id)
                stopwatch = StopWatch()
                self._storage.archive_study_output(study, output_id)
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
            ref_id=study.id,
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
        study = self._study_service.get_study(uuid)
        assert_permission(study, StudyPermissionType.READ)

        logger.info(download_log)
        file_download = self._file_transfer_manager.request_download(
            f"{study.name}-{uuid}-{output_id}{export_format.suffix}",
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
            mc_years,
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
            mc_years: list of monte-carlo years, if empty, all years are selected (only for mc-ind)
            on_success: callback to be called when the task is completed successfully
            on_failure: callback to be called when the task fails with an exception

        Returns:
            Aggregation task id
        """
        study = self._study_service.get_study(uuid)
        assert_permission(study, StudyPermissionType.READ)
        output_path = self._storage.get_output_path(study, output_id)
        aggregator_manager = AggregatorManager(
            output_path,
            query_file,
            frequency,
            ids_to_consider,
            columns_names,
            mc_years,
        )

        def aggregate_output_task(notifier: ITaskNotifier) -> TaskResult:
            try:
                stopwatch = StopWatch()
                stopwatch.log_elapsed(
                    lambda x: logger.info(f"Launch aggregation step for output '{output_id}' of study '{uuid}'.")
                )

                results = aggregator_manager.aggregate_output_data()
                export_df_chunks(self._study_service.config.storage.tmp_dir, file_path, results, export_format)

                stopwatch.log_elapsed(lambda x: logger.info(f"Store aggregation outputs in '{file_path}'."))

                if on_success:
                    on_success()

                stopwatch.log_elapsed(
                    lambda x: logger.info(f"Aggregated output file '{file_path}' is ready for download.")
                )
                return TaskResult(
                    success=True,
                    message=f"Successfully aggregated output data for study '{study.id}'."
                    f" Results are stored in '{file_path}'.",
                )

            except Exception as e:
                if on_failure:
                    on_failure(e)
                raise e

        task_id = self._task_service.add_task(
            aggregate_output_task,
            f"Aggregate output {output_id} of study {study.id}.",
            task_type=TaskType.OUTPUT_AGGREGATION,
            ref_id=study.id,
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
        study = self._study_service.get_study(study_id)
        assert_permission(study, StudyPermissionType.READ)

        output_variables: OutputVariables | None = db.session.get(OutputVariables, (study_id, output_id))
        if output_variables:
            return output_variables.to_model()

        # Fetches the data inside the FS
        output_path = self._storage.get_output_path(study, output_id)
        model = extract_variables_list(output_path)

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
        study = self._study_service.get_study(study_id)
        assert_permission(study, StudyPermissionType.READ)
        self._study_service.assert_study_unarchived(study)
        variables_list = self.get_output_variables_list(study_id, output_id)
        return OutputVariablesInformation.from_variables_list(variables_list)

    def get_output_variables_view(
        self,
        study_id: str,
        output_id: str,
        variable_type: OutputVariablesType,
        variable_name: str,
        frequency: MatrixFrequency,
        area_id: str | None = None,
        area_from_id: str | None = None,
        area_to_id: str | None = None,
        thermal_id: str | None = None,
        renewable_id: str | None = None,
        st_storage_id: str | None = None,
    ) -> pd.DataFrame:
        """
        If the view is already registered in DB, updates its `last_read` value and returns it.
        Else, raise an HTTP 404 error.
        """
        study = self._study_service.get_study(study_id)
        assert_permission(study, StudyPermissionType.READ)
        self._study_service.assert_study_unarchived(study)

        output_identifier = check_arguments_coherence_and_return_identifier(
            variable_type, output_id, area_id, area_from_id, area_to_id, thermal_id, renewable_id, st_storage_id
        )

        db_model = get_output_view_inside_db(
            study_id, output_id, variable_type, variable_name, frequency, output_identifier
        )
        if db_model is not None:
            # Update `last_read` value inside DB
            db_model.last_read = current_time()
            db.session.merge(db_model)
            db.session.commit()

            # Return the dataframe
            dataframe = self._matrix_service.get(db_model.matrix_id)
            dataframe.columns = pd.RangeIndex(len(dataframe.columns))  # type: ignore
            return dataframe

        # Checks if the asked couple `variable name` / `output_identifier` exists for the output
        available_variables = self.get_output_variables_list(study_id, output_id)
        check_output_variable_exists(output_id, variable_type, variable_name, available_variables, output_identifier)

        raise HTTPException(status_code=404, detail="The output variables view is not materialized in DB yet")

    def materialize_output_variables_view(
        self,
        study_id: str,
        output_id: str,
        variable_type: OutputVariablesType,
        variable_name: str,
        frequency: MatrixFrequency,
        area_id: str | None = None,
        area_from_id: str | None = None,
        area_to_id: str | None = None,
        thermal_id: str | None = None,
        renewable_id: str | None = None,
        st_storage_id: str | None = None,
    ) -> str:
        """
        If the view is already registered in DB, raise an HTTP Conflict error.
        Else, launch a task that fetches the required data and stores it inside the database.
        """
        study = self._study_service.get_study(study_id)
        assert_permission(study, StudyPermissionType.READ)
        self._study_service.assert_study_unarchived(study)

        output_identifier = check_arguments_coherence_and_return_identifier(
            variable_type, output_id, area_id, area_from_id, area_to_id, thermal_id, renewable_id, st_storage_id
        )

        db_model = get_output_view_inside_db(
            study_id, output_id, variable_type, variable_name, frequency, output_identifier
        )
        if db_model is not None:
            raise HTTPException(status_code=417, detail="The output variables view is already materialized in DB")

        # If a task materializing the same view is already running, returns its id
        task_name = f"Materializing output view for study `{study_id}`, output `{output_id}`, frequency `{frequency}`, id `{output_identifier.get_id_for_aggregation()}`"
        if sub_id := output_identifier.get_sub_id_for_aggregation():
            task_name += f" sub_id `{sub_id}`"

        study_tasks = self._task_service.list_tasks(
            TaskListFilter(
                ref_id=study_id,
                type=[TaskType.OUTPUT_VARIABLES_VIEW_MATERIALIZATION],
                status=[TaskStatus.RUNNING, TaskStatus.PENDING],
                name=task_name,
            )
        )
        if len(study_tasks) > 0:
            return study_tasks[0].id

        # Checks the asked couple `variable name` / `object_id` exists for the output
        available_variables = self.get_output_variables_list(study_id, output_id)
        check_output_variable_exists(output_id, variable_type, variable_name, available_variables, output_identifier)

        # Materialize the view
        task = OutputVariablesViewMaterializationTask(
            study_id, output_id, self, variable_type, variable_name, frequency, output_identifier
        )

        return self._task_service.add_task(
            task,
            task_name,
            task_type=TaskType.OUTPUT_VARIABLES_VIEW_MATERIALIZATION,
            ref_id=study_id,
            progress=0,
            custom_event_messages=None,
        )
