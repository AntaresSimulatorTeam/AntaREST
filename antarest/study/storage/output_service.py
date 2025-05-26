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
from typing import BinaryIO, Iterator, Optional, Sequence

import pandas as pd
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
from antarest.core.serde.json import to_json
from antarest.core.tasks.model import TaskListFilter, TaskResult, TaskStatus, TaskType
from antarest.core.tasks.service import ITaskNotifier, ITaskService
from antarest.core.utils.archives import ArchiveFormat
from antarest.core.utils.utils import StopWatch
from antarest.login.utils import get_user_id
from antarest.study.business.aggregator_management import (
    AggregatorManager,
    MCAllAreasQueryFile,
    MCAllLinksQueryFile,
    MCIndAreasQueryFile,
    MCIndLinksQueryFile,
)
from antarest.study.model import ExportFormat, Study, StudyDownloadDTO, StudySimResultDTO
from antarest.study.service import StudyService
from antarest.study.storage.output_storage import IOutputStorage
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.mcall.digest import (
    DigestSynthesis,
    DigestUI,
)
from antarest.study.storage.study_download_utils import StudyDownloader, get_output_variables_information
from antarest.study.storage.utils import assert_permission, is_managed, is_output_archived, remove_from_cache
from antarest.worker.archive_worker import ArchiveTaskArgs

logger = logging.getLogger(__name__)


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

    def unarchive_output(self, study_id: str, output_id: str, keep_src_zip: bool) -> Optional[str]:
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
                self._storage.unarchive_study_output(study, output_id, keep_src_zip)
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
                ArchiveTaskArgs(
                    src=str(src),
                    dest=str(dest),
                    remove_src=not keep_src_zip,
                ).model_dump(mode="json"),
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
            self.unarchive_output(uuid, output_id, not is_managed(study))

        return output_id

    def output_variables_information(self, study_uuid: str, output_uuid: str) -> dict[str, list[str]]:
        """
        Returns information about output variables using thematic and geographic trimming information
        Args:
            study_uuid: study id
            output_uuid: output id
        """
        study = self._study_service.get_study(study_uuid)
        assert_permission(study, StudyPermissionType.READ)
        self._study_service.assert_study_unarchived(study)
        return get_output_variables_information(self._study_service.get_file_study(study), output_uuid)

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
                json_response = to_json(matrix.model_dump(mode="json"))
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

    def archive_outputs(self, study_id: str) -> None:
        logger.info(f"Archiving all outputs for study {study_id}")
        study = self._study_service.get_study(study_id)
        assert_permission(study, StudyPermissionType.WRITE)
        self._study_service.assert_study_unarchived(study)
        file_study = self._study_service.get_file_study(study)
        for output in file_study.config.outputs:
            if not file_study.config.outputs[output].archived:
                self.archive_output(study_id, output)

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

    def aggregate_output_data(
        self,
        uuid: str,
        output_id: str,
        query_file: MCIndAreasQueryFile | MCAllAreasQueryFile | MCIndLinksQueryFile | MCAllLinksQueryFile,
        frequency: MatrixFrequency,
        columns_names: Sequence[str],
        ids_to_consider: Sequence[str],
        mc_years: Optional[Sequence[int]] = None,
    ) -> Iterator[pd.DataFrame]:
        """
        Aggregates output data based on several filtering conditions

        Args:
            uuid: study uuid
            output_id: simulation output ID
            query_file: which types of data to retrieve: "values", "details", "details-st-storage", "details-res", "ids"
            frequency: yearly, monthly, weekly, daily or hourly.
            columns_names: regexes (if details) or columns to be selected, if empty, all columns are selected
            ids_to_consider: list of areas or links ids to consider, if empty, all areas are selected
            mc_years: list of monte-carlo years, if empty, all years are selected (only for mc-ind)

        Returns: the aggregated data as a DataFrame

        """
        study = self._study_service.get_study(uuid)
        assert_permission(study, StudyPermissionType.READ)
        output_path = self._storage.get_output_path(study, output_id)
        aggregator_manager = AggregatorManager(
            output_path, query_file, frequency, ids_to_consider, columns_names, mc_years
        )
        return aggregator_manager.aggregate_output_data()
