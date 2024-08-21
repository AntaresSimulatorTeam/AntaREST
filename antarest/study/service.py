import base64
import collections
import contextlib
import http
import io
import json
import logging
import os
import time
import typing as t
from datetime import datetime, timedelta
from pathlib import Path, PurePosixPath
from uuid import uuid4

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.feather as feather
from fastapi import HTTPException, UploadFile
from markupsafe import escape
from starlette.responses import FileResponse, Response

from antarest.core.config import Config
from antarest.core.exceptions import (
    BadEditInstructionException,
    ChildNotFoundError,
    CommandApplicationError,
    IncorrectPathError,
    NotAManagedStudyException,
    ReferencedObjectDeletionNotAllowed,
    StudyDeletionNotAllowed,
    StudyNotFoundError,
    StudyTypeUnsupported,
    StudyVariantUpgradeError,
    TaskAlreadyRunning,
    UnsupportedOperationOnArchivedStudy,
)
from antarest.core.filetransfer.model import FileDownloadTaskDTO
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.interfaces.cache import ICache
from antarest.core.interfaces.eventbus import Event, EventType, IEventBus
from antarest.core.jwt import DEFAULT_ADMIN_USER, JWTGroup, JWTUser
from antarest.core.model import JSON, SUB_JSON, PermissionInfo, PublicMode, StudyPermissionType
from antarest.core.requests import RequestParameters, UserHasNotPermissionError
from antarest.core.tasks.model import TaskListFilter, TaskResult, TaskStatus, TaskType
from antarest.core.tasks.service import ITaskService, TaskUpdateNotifier, noop_notifier
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import StopWatch
from antarest.login.model import Group
from antarest.login.service import LoginService
from antarest.matrixstore.matrix_editor import MatrixEditInstruction
from antarest.study.business.adequacy_patch_management import AdequacyPatchManager
from antarest.study.business.advanced_parameters_management import AdvancedParamsManager
from antarest.study.business.aggregator_management import AggregatorManager, AreasQueryFile, LinksQueryFile
from antarest.study.business.allocation_management import AllocationManager
from antarest.study.business.area_management import AreaCreationDTO, AreaInfoDTO, AreaManager, AreaType, UpdateAreaUi
from antarest.study.business.areas.hydro_management import HydroManager
from antarest.study.business.areas.properties_management import PropertiesManager
from antarest.study.business.areas.renewable_management import RenewableManager
from antarest.study.business.areas.st_storage_management import STStorageManager
from antarest.study.business.areas.thermal_management import ThermalManager
from antarest.study.business.binding_constraint_management import BindingConstraintManager, ConstraintFilters, LinkTerm
from antarest.study.business.config_management import ConfigManager
from antarest.study.business.correlation_management import CorrelationManager
from antarest.study.business.district_manager import DistrictManager
from antarest.study.business.general_management import GeneralManager
from antarest.study.business.link_management import LinkInfoDTO, LinkManager
from antarest.study.business.matrix_management import MatrixManager, MatrixManagerError
from antarest.study.business.optimization_management import OptimizationManager
from antarest.study.business.playlist_management import PlaylistManager
from antarest.study.business.scenario_builder_management import ScenarioBuilderManager
from antarest.study.business.table_mode_management import TableModeManager
from antarest.study.business.thematic_trimming_management import ThematicTrimmingManager
from antarest.study.business.timeseries_config_management import TimeSeriesConfigManager
from antarest.study.business.utils import execute_or_add_commands
from antarest.study.business.xpansion_management import (
    GetXpansionSettings,
    UpdateXpansionSettings,
    XpansionCandidateDTO,
    XpansionManager,
)
from antarest.study.model import (
    DEFAULT_WORKSPACE_NAME,
    NEW_DEFAULT_STUDY_VERSION,
    STUDY_REFERENCE_TEMPLATES,
    CommentsDto,
    ExportFormat,
    MatrixIndex,
    PatchArea,
    PatchCluster,
    RawStudy,
    Study,
    StudyAdditionalData,
    StudyContentStatus,
    StudyDownloadDTO,
    StudyDownloadLevelDTO,
    StudyFolder,
    StudyMetadataDTO,
    StudyMetadataPatchDTO,
    StudySimResultDTO,
)
from antarest.study.repository import (
    AccessPermissions,
    StudyFilter,
    StudyMetadataRepository,
    StudyPagination,
    StudySortBy,
)
from antarest.study.storage.matrix_profile import adjust_matrix_columns_index
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfigDTO
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode
from antarest.study.storage.rawstudy.model.filesystem.inode import INode
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency
from antarest.study.storage.rawstudy.model.filesystem.matrix.output_series_matrix import OutputSeriesMatrix
from antarest.study.storage.rawstudy.model.filesystem.raw_file_node import RawFileNode
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.study_download_utils import StudyDownloader, get_output_variables_information
from antarest.study.storage.study_upgrader import StudyUpgrader, check_versions_coherence, find_next_version
from antarest.study.storage.utils import assert_permission, get_start_date, is_managed, remove_from_cache
from antarest.study.storage.variantstudy.business.utils import transform_command_to_dto
from antarest.study.storage.variantstudy.model.command.generate_thermal_cluster_timeseries import (
    GenerateThermalClusterTimeSeries,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.replace_matrix import ReplaceMatrix
from antarest.study.storage.variantstudy.model.command.update_comments import UpdateComments
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig
from antarest.study.storage.variantstudy.model.command.update_raw_file import UpdateRawFile
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy
from antarest.study.storage.variantstudy.model.model import CommandDTO
from antarest.study.storage.variantstudy.variant_study_service import VariantStudyService
from antarest.worker.archive_worker import ArchiveTaskArgs

logger = logging.getLogger(__name__)

MAX_MISSING_STUDY_TIMEOUT = 2  # days


def get_disk_usage(path: t.Union[str, Path]) -> int:
    """Calculate the total disk usage (in bytes) of a study in a compressed file or directory."""
    path = Path(path)
    if path.suffix.lower() in {".zip", ".7z"}:
        return os.path.getsize(path)
    total_size = 0
    with os.scandir(path) as it:
        for entry in it:
            if entry.is_file():
                total_size += entry.stat().st_size
            elif entry.is_dir():
                total_size += get_disk_usage(path=str(entry.path))
    return total_size


class ThermalClusterTimeSeriesGeneratorTask:
    """
    Task to generate thermal clusters time series
    """

    def __init__(
        self,
        _study_id: str,
        repository: StudyMetadataRepository,
        storage_service: StudyStorageService,
        event_bus: IEventBus,
    ):
        self._study_id = _study_id
        self.repository = repository
        self.storage_service = storage_service
        self.event_bus = event_bus

    def _generate_timeseries(self) -> None:
        """Run the task (lock the database)."""
        command_context = self.storage_service.variant_study_service.command_factory.command_context
        command = GenerateThermalClusterTimeSeries(command_context=command_context)
        with db():
            study = self.repository.one(self._study_id)
            file_study = self.storage_service.get_storage(study).get_raw(study)
            execute_or_add_commands(study, file_study, [command], self.storage_service)
            self.event_bus.push(
                Event(
                    type=EventType.STUDY_EDITED,
                    payload=study.to_json_summary(),
                    permissions=PermissionInfo.from_study(study),
                )
            )

    def run_task(self, notifier: TaskUpdateNotifier) -> TaskResult:
        msg = f"Generating thermal timeseries for study '{self._study_id}'"
        notifier(msg)
        self._generate_timeseries()
        msg = f"Successfully generated thermal timeseries for study '{self._study_id}'"
        notifier(msg)
        return TaskResult(success=True, message=msg)

    # Make `ThermalClusterTimeSeriesGeneratorTask` object callable
    __call__ = run_task


class StudyUpgraderTask:
    """
    Task to perform a study upgrade.
    """

    def __init__(
        self,
        study_id: str,
        target_version: str,
        *,
        repository: StudyMetadataRepository,
        storage_service: StudyStorageService,
        cache_service: ICache,
        event_bus: IEventBus,
    ):
        self._study_id = study_id
        self._target_version = target_version
        self.repository = repository
        self.storage_service = storage_service
        self.cache_service = cache_service
        self.event_bus = event_bus

    def _upgrade_study(self) -> None:
        """Run the task (lock the database)."""
        study_id: str = self._study_id
        target_version: str = self._target_version
        is_study_denormalized = False
        with db():
            # TODO We want to verify that a study doesn't have children and if it does do we upgrade all of them ?
            study_to_upgrade = self.repository.one(study_id)
            is_variant = isinstance(study_to_upgrade, VariantStudy)
            try:
                # sourcery skip: extract-method
                if is_variant:
                    self.storage_service.variant_study_service.clear_snapshot(study_to_upgrade)
                else:
                    study_path = Path(study_to_upgrade.path)
                    study_upgrader = StudyUpgrader(study_path, target_version)
                    if is_managed(study_to_upgrade) and study_upgrader.should_denormalize_study():
                        # We have to denormalize the study because the upgrade impacts study matrices
                        file_study = self.storage_service.get_storage(study_to_upgrade).get_raw(study_to_upgrade)
                        file_study.tree.denormalize()
                        is_study_denormalized = True
                    study_upgrader.upgrade()
                remove_from_cache(self.cache_service, study_to_upgrade.id)
                study_to_upgrade.version = target_version
                self.repository.save(study_to_upgrade)
                self.event_bus.push(
                    Event(
                        type=EventType.STUDY_EDITED,
                        payload=study_to_upgrade.to_json_summary(),
                        permissions=PermissionInfo.from_study(study_to_upgrade),
                    )
                )
            finally:
                if is_study_denormalized:
                    file_study = self.storage_service.get_storage(study_to_upgrade).get_raw(study_to_upgrade)
                    file_study.tree.normalize()

    def run_task(self, notifier: TaskUpdateNotifier) -> TaskResult:
        """
        Run the study upgrade task.

        Args:
            notifier: function used to emit user messages.

        Returns:
            The result of the task is always `success=True`.
        """
        # The call to `_upgrade_study` may raise an exception, which will be
        # handled in the task service (see: `TaskJobService._run_task`)
        msg = f"Upgrade study '{self._study_id}' to version {self._target_version}"
        notifier(msg)
        self._upgrade_study()
        msg = f"Successfully upgraded study '{self._study_id}' to version {self._target_version}"
        notifier(msg)
        return TaskResult(success=True, message=msg)

    # Make `StudyUpgraderTask` object is callable
    __call__ = run_task


class StudyService:
    """
    Storage module facade service to handle studies management.
    """

    def __init__(
        self,
        raw_study_service: RawStudyService,
        variant_study_service: VariantStudyService,
        user_service: LoginService,
        repository: StudyMetadataRepository,
        event_bus: IEventBus,
        file_transfer_manager: FileTransferManager,
        task_service: ITaskService,
        cache_service: ICache,
        config: Config,
    ):
        self.storage_service = StudyStorageService(raw_study_service, variant_study_service)
        self.user_service = user_service
        self.repository = repository
        self.event_bus = event_bus
        self.file_transfer_manager = file_transfer_manager
        self.task_service = task_service
        self.areas = AreaManager(self.storage_service, self.repository)
        self.district_manager = DistrictManager(self.storage_service)
        self.links = LinkManager(self.storage_service)
        self.config_manager = ConfigManager(self.storage_service)
        self.general_manager = GeneralManager(self.storage_service)
        self.thematic_trimming_manager = ThematicTrimmingManager(self.storage_service)
        self.optimization_manager = OptimizationManager(self.storage_service)
        self.adequacy_patch_manager = AdequacyPatchManager(self.storage_service)
        self.advanced_parameters_manager = AdvancedParamsManager(self.storage_service)
        self.hydro_manager = HydroManager(self.storage_service)
        self.allocation_manager = AllocationManager(self.storage_service)
        self.properties_manager = PropertiesManager(self.storage_service)
        self.renewable_manager = RenewableManager(self.storage_service)
        self.thermal_manager = ThermalManager(self.storage_service)
        self.st_storage_manager = STStorageManager(self.storage_service)
        self.ts_config_manager = TimeSeriesConfigManager(self.storage_service)
        self.playlist_manager = PlaylistManager(self.storage_service)
        self.scenario_builder_manager = ScenarioBuilderManager(self.storage_service)
        self.xpansion_manager = XpansionManager(self.storage_service)
        self.matrix_manager = MatrixManager(self.storage_service)
        self.binding_constraint_manager = BindingConstraintManager(self.storage_service)
        self.correlation_manager = CorrelationManager(self.storage_service)
        self.table_mode_manager = TableModeManager(
            self.areas,
            self.links,
            self.thermal_manager,
            self.renewable_manager,
            self.st_storage_manager,
            self.binding_constraint_manager,
        )
        self.cache_service = cache_service
        self.config = config
        self.on_deletion_callbacks: t.List[t.Callable[[str], None]] = []

    def add_on_deletion_callback(self, callback: t.Callable[[str], None]) -> None:
        self.on_deletion_callbacks.append(callback)

    def _on_study_delete(self, uuid: str) -> None:
        """Run all callbacks"""
        for callback in self.on_deletion_callbacks:
            callback(uuid)

    def get(self, uuid: str, url: str, depth: int, params: RequestParameters, format: t.Optional[str] = None) -> JSON:
        """
        Get study data inside filesystem
        Args:
            uuid: study uuid
            url: route to follow inside study structure
            depth: depth to expand tree when route matched
            format: Indicates the file return format. Can be 'json', 'arrow' or None. If None, the file will be returned as is.
            params: request parameters

        Returns: data study formatted in json

        """
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.READ)

        return self.storage_service.get_storage(study).get(study, url, depth, format)

    def aggregate_output_data(
        self,
        uuid: str,
        output_id: str,
        query_file: t.Union[AreasQueryFile, LinksQueryFile],
        frequency: MatrixFrequency,
        mc_years: t.Sequence[int],
        columns_names: t.Sequence[str],
        ids_to_consider: t.Sequence[str],
        params: RequestParameters,
    ) -> pd.DataFrame:
        """
        Aggregates output data based on several filtering conditions
        Args:
            uuid: study uuid
            output_id: simulation output ID
            query_file: which types of data to retrieve ("values", "details", "details-st-storage", "details-res")
            frequency: yearly, monthly, weekly, daily or hourly.
            mc_years: list of monte-carlo years, if empty, all years are selected
            columns_names: columns to be selected, if empty, all columns are selected
            ids_to_consider: list of areas or links ids to consider, if empty, all areas are selected
            params: request parameters

        Returns: the aggregated data as a DataFrame

        """
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.READ)
        study_path = self.storage_service.raw_study_service.get_study_path(study)
        # fmt: off
        aggregator_manager = AggregatorManager(
            study_path,
            output_id,
            query_file,
            frequency,
            mc_years,
            columns_names,
            ids_to_consider
        )
        # fmt: on
        return aggregator_manager.aggregate_output_data()

    def get_logs(
        self,
        study_id: str,
        output_id: str,
        job_id: str,
        err_log: bool,
        params: RequestParameters,
    ) -> t.Optional[str]:
        study = self.get_study(study_id)
        assert_permission(params.user, study, StudyPermissionType.READ)
        file_study = self.storage_service.get_storage(study).get_raw(study)
        log_locations = {
            False: [
                ["output", "logs", f"{job_id}-out.log"],
                ["output", "logs", f"{output_id}-out.log"],
                ["output", output_id, "antares-out"],
                ["output", output_id, "simulation"],
            ],
            True: [
                ["output", "logs", f"{job_id}-err.log"],
                ["output", "logs", f"{output_id}-err.log"],
                ["output", output_id, "antares-err"],
            ],
        }
        empty_log = False
        for log_location in log_locations[err_log]:
            try:
                log = t.cast(
                    bytes,
                    file_study.tree.get(log_location, depth=1, format="json"),
                ).decode(encoding="utf-8")
                # when missing file, RawFileNode return empty bytes
                if log:
                    return log
                else:
                    empty_log = True
            except ChildNotFoundError:
                pass
            except KeyError:
                pass
        if empty_log:
            return ""
        raise ChildNotFoundError(f"Logs for {output_id} of study {study_id} were not found")

    def save_logs(
        self,
        study_id: str,
        job_id: str,
        log_suffix: str,
        log_data: str,
    ) -> None:
        logger.info(f"Saving logs for job {job_id} of study {study_id}")
        stopwatch = StopWatch()
        study = self.get_study(study_id)
        file_study = self.storage_service.get_storage(study).get_raw(study)
        file_study.tree.save(
            bytes(log_data, encoding="utf-8"),
            [
                "output",
                "logs",
                f"{job_id}-{log_suffix}",
            ],
        )
        stopwatch.log_elapsed(lambda d: logger.info(f"Saved logs for job {job_id} in {d}s"))

    def get_comments(self, study_id: str, params: RequestParameters) -> t.Union[str, JSON]:
        """
        Get the comments of a study.

        Args:
            study_id: The ID of the study.
            params: The parameters of the HTTP request containing the user information.

        Returns: textual comments of the study.
        """
        study = self.get_study(study_id)
        assert_permission(params.user, study, StudyPermissionType.READ)

        output = self.storage_service.get_storage(study).get(metadata=study, url="/settings/comments")

        with contextlib.suppress(AttributeError, UnicodeDecodeError):
            output = output.decode("utf-8")  # type: ignore

        return output

    def edit_comments(
        self,
        uuid: str,
        data: CommentsDto,
        params: RequestParameters,
    ) -> None:
        """
        Replace data inside study.

        Args:
            uuid: study id
            data: new data to replace
            params: request parameters

        Returns: new data replaced

        """
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.WRITE)
        self._assert_study_unarchived(study)

        if isinstance(study, RawStudy):
            self.edit_study(
                uuid=uuid,
                url="settings/comments",
                new=bytes(data.comments, "utf-8"),
                params=params,
            )
        else:
            variant_study_service = self.storage_service.variant_study_service
            command = [
                UpdateRawFile(
                    target="settings/comments",
                    b64Data=base64.b64encode(data.comments.encode("utf-8")).decode("utf-8"),
                    command_context=variant_study_service.command_factory.command_context,
                )
            ]
            variant_study_service.append_commands(
                study.id,
                transform_command_to_dto(command, force_aggregate=True),
                RequestParameters(user=params.user),
            )

    def get_studies_information(
        self,
        study_filter: StudyFilter,
        sort_by: t.Optional[StudySortBy] = None,
        pagination: StudyPagination = StudyPagination(),
    ) -> t.Dict[str, StudyMetadataDTO]:
        """
        Get information for matching studies of a search query.
        Args:
            study_filter: filtering parameters
            sort_by: how to sort the db query results
            pagination: set offset and limit for db query

        Returns: List of study information
        """
        logger.info("Retrieving matching studies")
        studies: t.Dict[str, StudyMetadataDTO] = {}
        matching_studies = self.repository.get_all(
            study_filter=study_filter,
            sort_by=sort_by,
            pagination=pagination,
        )
        logger.info("Studies retrieved")
        for study in matching_studies:
            study_metadata = self._try_get_studies_information(study)
            if study_metadata is not None:
                studies[study_metadata.id] = study_metadata
        return studies

    def count_studies(
        self,
        study_filter: StudyFilter,
    ) -> int:
        """
        Get number of matching studies.
        Args:
            study_filter: filtering parameters

        Returns: total number of studies matching the filtering criteria
        """
        total: int = self.repository.count_studies(
            study_filter=study_filter,
        )
        return total

    def _try_get_studies_information(self, study: Study) -> t.Optional[StudyMetadataDTO]:
        try:
            return self.storage_service.get_storage(study).get_study_information(study)
        except Exception as e:
            logger.warning(
                "Failed to build study %s (%s) metadata",
                study.id,
                study.path,
                exc_info=e,
            )
        return None

    def get_study_information(self, uuid: str, params: RequestParameters) -> StudyMetadataDTO:
        """
        Retrieve study information.

        Args:
            uuid: The UUID of the study.
            params: The request parameters.

        Returns:
            Information about the study.
        """
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.READ)
        logger.info("Study metadata requested for study %s by user %s", uuid, params.get_user_id())
        # TODO: Debounce this with an "update_study_last_access" method updating only every few seconds.
        study.last_access = datetime.utcnow()
        self.repository.save(study)
        return self.storage_service.get_storage(study).get_study_information(study)

    def update_study_information(
        self,
        uuid: str,
        metadata_patch: StudyMetadataPatchDTO,
        params: RequestParameters,
    ) -> StudyMetadataDTO:
        """
        Update study metadata
        Args:
            uuid: study uuid
            metadata_patch: metadata patch
            params: request parameters
        """
        logger.info(
            "updating study %s metadata for user %s",
            uuid,
            params.get_user_id(),
        )
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.WRITE)

        if metadata_patch.horizon:
            study_settings_url = "settings/generaldata/general"
            self._assert_study_unarchived(study)
            study_settings = self.storage_service.get_storage(study).get(study, study_settings_url)
            study_settings["horizon"] = metadata_patch.horizon
            self._edit_study_using_command(study=study, url=study_settings_url, data=study_settings)

        if metadata_patch.author:
            study_antares_url = "study/antares"
            self._assert_study_unarchived(study)
            study_antares = self.storage_service.get_storage(study).get(study, study_antares_url)
            study_antares["author"] = metadata_patch.author
            self._edit_study_using_command(study=study, url=study_antares_url, data=study_antares)

        study.additional_data = study.additional_data or StudyAdditionalData()
        if metadata_patch.name:
            study.name = metadata_patch.name
        if metadata_patch.author:
            study.additional_data.author = metadata_patch.author
        if metadata_patch.horizon:
            study.additional_data.horizon = metadata_patch.horizon
        if metadata_patch.tags:
            self.repository.update_tags(study, metadata_patch.tags)

        new_metadata = self.storage_service.get_storage(study).patch_update_study_metadata(study, metadata_patch)

        self.event_bus.push(
            Event(
                type=EventType.STUDY_DATA_EDITED,
                payload=study.to_json_summary(),
                permissions=PermissionInfo.from_study(study),
            )
        )

        return new_metadata

    def check_study_access(
        self,
        uuid: str,
        permission: StudyPermissionType,
        params: RequestParameters,
    ) -> Study:
        study = self.get_study(uuid)
        assert_permission(params.user, study, permission)
        self._assert_study_unarchived(study)
        return study

    def get_study_path(self, uuid: str, params: RequestParameters) -> Path:
        """
        Retrieve study path
        Args:
            uuid: study uuid
            params: request parameters

        Returns:

        """
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.RUN)

        logger.info("study %s path asked by user %s", uuid, params.get_user_id())
        return self.storage_service.get_storage(study).get_study_path(study)

    def create_study(
        self,
        study_name: str,
        version: t.Optional[str],
        group_ids: t.List[str],
        params: RequestParameters,
    ) -> str:
        """
        Creates a study with the specified study name, version, group IDs, and user parameters.

        Args:
            study_name: The name of the study to create.
            version: The version number of the study to choose the template for creation.
            group_ids: A possibly empty list of user group IDs to associate with the study.
            params:
                The parameters of the HTTP request for creation, used to determine
                the currently logged-in user (ID and name).

        Returns:
            str: The ID of the newly created study.
        """
        sid = str(uuid4())
        study_path = self.config.get_workspace_path() / sid

        author = self.get_user_name(params)

        raw = RawStudy(
            id=sid,
            name=study_name,
            workspace=DEFAULT_WORKSPACE_NAME,
            path=str(study_path),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            version=version or NEW_DEFAULT_STUDY_VERSION,
            additional_data=StudyAdditionalData(author=author),
        )

        raw = self.storage_service.raw_study_service.create(raw)
        self._save_study(raw, params.user, group_ids)
        self.event_bus.push(
            Event(
                type=EventType.STUDY_CREATED,
                payload=raw.to_json_summary(),
                permissions=PermissionInfo.from_study(raw),
            )
        )

        logger.info("study %s created by user %s", raw.id, params.get_user_id())
        return str(raw.id)

    def get_user_name(self, params: RequestParameters) -> str:
        """
        Retrieves the name of a user based on the provided request parameters.

        Args:
            params: The request parameters which includes user information.

        Returns:
            Returns the user's name or, if the logged user is a "bot"
            (i.e., an application's token), it returns the token's author name.
        """
        if params.user:
            user_id = params.user.impersonator if params.user.type == "bots" else params.user.id
            if curr_user := self.user_service.get_user(user_id, params):
                return curr_user.to_dto().name
        return "Unknown"

    def get_study_synthesis(self, study_id: str, params: RequestParameters) -> FileStudyTreeConfigDTO:
        """
        Get the synthesis of a study.

        Args:
            study_id: The ID of the study.
            params: The parameters of the HTTP request containing the user information.

        Returns: study synthesis
        """
        study = self.get_study(study_id)
        assert_permission(params.user, study, StudyPermissionType.READ)
        study.last_access = datetime.utcnow()
        self.repository.save(study)
        study_storage_service = self.storage_service.get_storage(study)
        return study_storage_service.get_synthesis(study, params)

    def get_input_matrix_startdate(
        self, study_id: str, path: t.Optional[str], params: RequestParameters
    ) -> MatrixIndex:
        study = self.get_study(study_id)
        assert_permission(params.user, study, StudyPermissionType.READ)
        file_study = self.storage_service.get_storage(study).get_raw(study)
        output_id = None
        level = StudyDownloadLevelDTO.HOURLY
        if path:
            path_components = path.strip().strip("/").split("/")
            if len(path_components) > 2 and path_components[0] == "output":
                output_id = path_components[1]
            data_node = file_study.tree.get_node(path_components)
            if isinstance(data_node, OutputSeriesMatrix) or isinstance(data_node, InputSeriesMatrix):
                level = StudyDownloadLevelDTO(data_node.freq)
        return get_start_date(file_study, output_id, level)

    def remove_duplicates(self) -> None:
        duplicates = self.repository.list_duplicates()
        ids: t.List[str] = []
        # ids with same path
        duplicates_by_path = collections.defaultdict(list)
        for study_id, path in duplicates:
            duplicates_by_path[path].append(study_id)
        for path, study_ids in duplicates_by_path.items():
            ids.extend(study_ids[1:])
        if ids:  # Check if ids is not empty
            self.repository.delete(*ids)

    def sync_studies_on_disk(self, folders: t.List[StudyFolder], directory: t.Optional[Path] = None) -> None:
        """
        Used by watcher to send list of studies present on filesystem.

        Args:
            folders: list of studies currently present on folder
            directory: directory of studies that will be watched

        Returns:

        """
        now = datetime.utcnow()
        clean_up_missing_studies_threshold = now - timedelta(days=MAX_MISSING_STUDY_TIMEOUT)
        all_studies = self.repository.get_all_raw()
        if directory:
            all_studies = [raw_study for raw_study in all_studies if directory in Path(raw_study.path).parents]
        studies_by_path = {study.path: study for study in all_studies}

        # delete orphan studies on database
        paths = [str(f.path) for f in folders]
        for study in all_studies:
            if (
                isinstance(study, RawStudy)
                and not study.archived
                and (study.workspace != DEFAULT_WORKSPACE_NAME and study.path not in paths)
            ):
                if not study.missing:
                    logger.info(
                        "Study %s at %s is not present in disk and will be marked for deletion in %i days",
                        study.id,
                        study.path,
                        MAX_MISSING_STUDY_TIMEOUT,
                    )
                    study.missing = now
                    self.repository.save(study)
                    self.event_bus.push(
                        Event(
                            type=EventType.STUDY_DELETED,
                            payload=study.to_json_summary(),
                            permissions=PermissionInfo.from_study(study),
                        )
                    )
                elif study.missing < clean_up_missing_studies_threshold:
                    logger.info(
                        "Study %s at %s is not present in disk and will be deleted",
                        study.id,
                        study.path,
                    )
                    self.repository.delete(study.id)

        # Add new studies
        study_paths = [study.path for study in all_studies if study.missing is None]
        missing_studies = {study.path: study for study in all_studies if study.missing is not None}
        for folder in folders:
            study_path = str(folder.path)
            if study_path not in study_paths:
                try:
                    if study_path not in missing_studies.keys():
                        base_path = self.config.storage.workspaces[folder.workspace].path
                        dir_name = folder.path.relative_to(base_path)
                        study = RawStudy(
                            id=str(uuid4()),
                            name=folder.path.name,
                            path=study_path,
                            folder=str(dir_name),
                            workspace=folder.workspace,
                            owner=None,
                            groups=folder.groups,
                            public_mode=PublicMode.FULL if len(folder.groups) == 0 else PublicMode.NONE,
                        )
                        logger.info(
                            "Study at %s appears on disk and will be added as %s",
                            study.path,
                            study.id,
                        )
                    else:
                        study = missing_studies[study_path]
                        study.missing = None
                        logger.info(
                            "Study at %s re appears on disk and will be added as %s",
                            study.path,
                            study.id,
                        )

                    self.storage_service.raw_study_service.update_from_raw_meta(study, fallback_on_default=True)

                    logger.warning("Skipping study format error analysis")
                    # TODO re enable this on an async worker
                    # study.content_status = self._analyse_study(study)

                    self.repository.save(study)
                    self.event_bus.push(
                        Event(
                            type=EventType.STUDY_CREATED,
                            payload=study.to_json_summary(),
                            permissions=PermissionInfo.from_study(study),
                        )
                    )
                except Exception as e:
                    logger.error(f"Failed to add study {folder.path}", exc_info=e)
            elif directory and study_path in studies_by_path:
                existing_study = studies_by_path[study_path]
                if self.storage_service.raw_study_service.update_name_and_version_from_raw_meta(existing_study):
                    self.repository.save(existing_study)

    def copy_study(
        self,
        src_uuid: str,
        dest_study_name: str,
        group_ids: t.List[str],
        use_task: bool,
        params: RequestParameters,
        with_outputs: bool = False,
    ) -> str:
        """
        Copy study to another location.

        Args:
            src_uuid: source study
            dest_study_name: destination study
            group_ids: group to attach on new study
            params: request parameters
            with_outputs: Indicates whether the study's outputs should also be duplicated.
            use_task: indicate if the task job service should be used

        Returns:
            The unique identifier of the task copying the study.
        """
        src_study = self.get_study(src_uuid)
        assert_permission(params.user, src_study, StudyPermissionType.READ)
        self._assert_study_unarchived(src_study)

        def copy_task(notifier: TaskUpdateNotifier) -> TaskResult:
            origin_study = self.get_study(src_uuid)
            study = self.storage_service.get_storage(origin_study).copy(
                origin_study,
                dest_study_name,
                group_ids,
                with_outputs,
            )
            self._save_study(study, params.user, group_ids)
            self.event_bus.push(
                Event(
                    type=EventType.STUDY_CREATED,
                    payload=study.to_json_summary(),
                    permissions=PermissionInfo.from_study(study),
                )
            )

            logger.info(
                "study %s copied to %s by user %s",
                origin_study,
                study.id,
                params.get_user_id(),
            )
            return TaskResult(
                success=True,
                message=f"Study {src_uuid} successfully copied to {study.id}",
                return_value=study.id,
            )

        if use_task:
            task_or_study_id = self.task_service.add_task(
                copy_task,
                f"Study {src_study.name} ({src_uuid}) copy",
                task_type=TaskType.COPY,
                ref_id=src_study.id,
                custom_event_messages=None,
                request_params=params,
            )
        else:
            res = copy_task(noop_notifier)
            task_or_study_id = res.return_value or ""

        return task_or_study_id

    def move_study(self, study_id: str, new_folder: str, params: RequestParameters) -> None:
        study = self.get_study(study_id)
        assert_permission(params.user, study, StudyPermissionType.WRITE)
        if not is_managed(study):
            raise NotAManagedStudyException(study_id)
        study.folder = new_folder
        self.repository.save(study, update_modification_date=False)
        self.event_bus.push(
            Event(
                type=EventType.STUDY_EDITED,
                payload=study.to_json_summary(),
                permissions=PermissionInfo.from_study(study),
            )
        )

    def export_study(
        self,
        uuid: str,
        params: RequestParameters,
        outputs: bool = True,
    ) -> FileDownloadTaskDTO:
        """
        Export study to a zip file.
        Args:
            uuid: study id
            params: request parameters
            outputs: integrate output folder in zip file

        """
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.READ)
        self._assert_study_unarchived(study)

        logger.info("Exporting study %s", uuid)
        export_name = f"Study {study.name} ({uuid}) export"
        export_file_download = self.file_transfer_manager.request_download(
            f"{study.name}-{uuid}.zip", export_name, params.user
        )
        export_path = Path(export_file_download.path)
        export_id = export_file_download.id

        def export_task(notifier: TaskUpdateNotifier) -> TaskResult:
            try:
                target_study = self.get_study(uuid)
                self.storage_service.get_storage(target_study).export_study(target_study, export_path, outputs)
                self.file_transfer_manager.set_ready(export_id)
                return TaskResult(success=True, message=f"Study {uuid} successfully exported")
            except Exception as e:
                self.file_transfer_manager.fail(export_id, str(e))
                raise e

        task_id = self.task_service.add_task(
            export_task,
            export_name,
            task_type=TaskType.EXPORT,
            ref_id=study.id,
            custom_event_messages=None,
            request_params=params,
        )

        return FileDownloadTaskDTO(file=export_file_download.to_dto(), task=task_id)

    def output_variables_information(
        self,
        study_uuid: str,
        output_uuid: str,
        params: RequestParameters,
    ) -> t.Dict[str, t.List[str]]:
        """
        Returns information about output variables using thematic and geographic trimming information
        Args:
            study_uuid: study id
            output_uuid: output id
            params: request parameters
        """
        study = self.get_study(study_uuid)
        assert_permission(params.user, study, StudyPermissionType.READ)
        self._assert_study_unarchived(study)
        return get_output_variables_information(self.storage_service.get_storage(study).get_raw(study), output_uuid)

    def export_output(
        self,
        study_uuid: str,
        output_uuid: str,
        params: RequestParameters,
    ) -> FileDownloadTaskDTO:
        """
        Export study output to a zip file.
        Args:
            study_uuid: study id
            output_uuid: output id
            params: request parameters
        """
        study = self.get_study(study_uuid)
        assert_permission(params.user, study, StudyPermissionType.READ)
        self._assert_study_unarchived(study)

        logger.info(f"Exporting {output_uuid} from study {study_uuid}")
        export_name = f"Study output {study.name}/{output_uuid} export"
        export_file_download = self.file_transfer_manager.request_download(
            f"{study.name}-{study_uuid}-{output_uuid}.zip",
            export_name,
            params.user,
        )
        export_path = Path(export_file_download.path)
        export_id = export_file_download.id

        def export_task(notifier: TaskUpdateNotifier) -> TaskResult:
            try:
                target_study = self.get_study(study_uuid)
                self.storage_service.get_storage(target_study).export_output(
                    metadata=target_study,
                    output_id=output_uuid,
                    target=export_path,
                )
                self.file_transfer_manager.set_ready(export_id)
                return TaskResult(
                    success=True,
                    message=f"Study output {study_uuid}/{output_uuid} successfully exported",
                )
            except Exception as e:
                self.file_transfer_manager.fail(export_id, str(e))
                raise e

        task_id = self.task_service.add_task(
            export_task,
            export_name,
            task_type=TaskType.EXPORT,
            ref_id=study.id,
            custom_event_messages=None,
            request_params=params,
        )

        return FileDownloadTaskDTO(file=export_file_download.to_dto(), task=task_id)

    def export_study_flat(
        self,
        uuid: str,
        params: RequestParameters,
        dest: Path,
        output_list: t.Optional[t.List[str]] = None,
    ) -> None:
        logger.info(f"Flat exporting study {uuid}")
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.READ)
        self._assert_study_unarchived(study)

        return self.storage_service.get_storage(study).export_study_flat(
            study, dest, len(output_list or []) > 0, output_list
        )

    def delete_study(self, uuid: str, children: bool, params: RequestParameters) -> None:
        """
        Delete study and all its children

        Args:
            uuid: study uuid
            children: delete children or not
            params: request parameters
        """
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.WRITE)

        study_info = study.to_json_summary()

        # this prefetch the workspace because it is lazy loaded and the object is deleted
        # before using workspace attribute in raw study deletion
        # see https://github.com/AntaresSimulatorTeam/AntaREST/issues/606
        if isinstance(study, RawStudy):
            _ = study.workspace

        if self.storage_service.variant_study_service.has_children(study):
            if children:
                self.storage_service.variant_study_service.walk_children(
                    study.id,
                    lambda v: self.delete_study(v.id, True, params),
                    bottom_first=True,
                )
                return
            else:
                raise StudyDeletionNotAllowed(study.id, "Study has variant children")

        self.repository.delete(study.id)

        self.event_bus.push(
            Event(
                type=EventType.STUDY_DELETED,
                payload=study_info,
                permissions=PermissionInfo.from_study(study),
            )
        )

        # delete the files afterward for
        # if the study cannot be deleted from database for foreign key reason
        if self._assert_study_unarchived(study=study, raise_exception=False):
            self.storage_service.get_storage(study).delete(study)
        else:
            if isinstance(study, RawStudy):
                os.unlink(self.storage_service.raw_study_service.get_archive_path(study))

        logger.info("study %s deleted by user %s", uuid, params.get_user_id())

        self._on_study_delete(uuid=uuid)

    def delete_output(self, uuid: str, output_name: str, params: RequestParameters) -> None:
        """
        Delete specific output simulation in study
        Args:
            uuid: study uuid
            output_name: output simulation name
            params: request parameters

        Returns:

        """
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.WRITE)
        self._assert_study_unarchived(study)
        self.storage_service.get_storage(study).delete_output(study, output_name)
        self.event_bus.push(
            Event(
                type=EventType.STUDY_DATA_EDITED,
                payload=study.to_json_summary(),
                permissions=PermissionInfo.from_study(study),
            )
        )

        logger.info(f"Output {output_name} deleted from study {uuid}")

    def download_outputs(
        self,
        study_id: str,
        output_id: str,
        data: StudyDownloadDTO,
        use_task: bool,
        filetype: ExportFormat,
        params: RequestParameters,
        tmp_export_file: t.Optional[Path] = None,
    ) -> t.Union[Response, FileDownloadTaskDTO, FileResponse]:
        """
        Download outputs
        Args:
            study_id: study ID.
            output_id: output ID.
            data: Json parameters.
            use_task: use task or not.
            filetype: type of returning file,.
            tmp_export_file: temporary file (if `use_task` is false),.
            params: request parameters.

        Returns: CSV content file

        """
        # GET STUDY ID
        study = self.get_study(study_id)
        assert_permission(params.user, study, StudyPermissionType.READ)
        self._assert_study_unarchived(study)
        logger.info(f"Study {study_id} output download asked by {params.get_user_id()}")

        if use_task:
            logger.info(f"Exporting {output_id} from study {study_id}")
            export_name = f"Study filtered output {study.name}/{output_id} export"
            export_file_download = self.file_transfer_manager.request_download(
                f"{study.name}-{study_id}-{output_id}_filtered{filetype.suffix}",
                export_name,
                params.user,
            )
            export_path = Path(export_file_download.path)
            export_id = export_file_download.id

            def export_task(_notifier: TaskUpdateNotifier) -> TaskResult:
                try:
                    _study = self.get_study(study_id)
                    _stopwatch = StopWatch()
                    _matrix = StudyDownloader.build(
                        self.storage_service.get_storage(_study).get_raw(_study),
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
                    self.file_transfer_manager.set_ready(export_id)
                    return TaskResult(
                        success=True,
                        message=f"Study filtered output {study_id}/{output_id} successfully exported",
                    )
                except Exception as e:
                    self.file_transfer_manager.fail(export_id, str(e))
                    raise

            task_id = self.task_service.add_task(
                export_task,
                export_name,
                task_type=TaskType.EXPORT,
                ref_id=study.id,
                custom_event_messages=None,
                request_params=params,
            )

            return FileDownloadTaskDTO(file=export_file_download.to_dto(), task=task_id)
        else:
            stopwatch = StopWatch()
            matrix = StudyDownloader.build(
                self.storage_service.get_storage(study).get_raw(study),
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
                json_response = json.dumps(
                    matrix.dict(),
                    ensure_ascii=False,
                    allow_nan=True,
                    indent=None,
                    separators=(",", ":"),
                ).encode("utf-8")
                return Response(content=json_response, media_type="application/json")

    def get_study_sim_result(self, study_id: str, params: RequestParameters) -> t.List[StudySimResultDTO]:
        """
        Get global result information
        Args:
            study_id: study Id
            params: request parameters

        Returns: an object containing all needed information

        """
        study = self.get_study(study_id)
        assert_permission(params.user, study, StudyPermissionType.READ)
        logger.info(
            "study %s output listing asked by user %s",
            study_id,
            params.get_user_id(),
        )

        return self.storage_service.get_storage(study).get_study_sim_result(study)

    def set_sim_reference(
        self,
        study_id: str,
        output_id: str,
        status: bool,
        params: RequestParameters,
    ) -> None:
        """
        Set simulation as the reference output.

        Args:
            study_id: study ID.
            output_id: The ID of the output to set as reference.
            status: state of the reference status.
            params: request parameters
        """
        study = self.get_study(study_id)
        assert_permission(params.user, study, StudyPermissionType.WRITE)
        self._assert_study_unarchived(study)

        logger.info(
            f"output {output_id} set by user {params.get_user_id()} as reference ({status}) for study {study_id}"
        )

        self.storage_service.get_storage(study).set_reference_output(study, output_id, status)

    def import_study(
        self,
        stream: t.BinaryIO,
        group_ids: t.List[str],
        params: RequestParameters,
    ) -> str:
        """
        Import a compressed study.

        Args:
            stream: binary content of the study compressed in ZIP or 7z format.
            group_ids: group to attach to study
            params: request parameters

        Returns:
            New study UUID.

        Raises:
            BadArchiveContent: If the archive is corrupted or in an unknown format.
        """
        sid = str(uuid4())
        path = str(self.config.get_workspace_path() / sid)
        study = RawStudy(
            id=sid,
            workspace=DEFAULT_WORKSPACE_NAME,
            path=path,
            additional_data=StudyAdditionalData(),
            public_mode=PublicMode.NONE if group_ids else PublicMode.READ,
            groups=group_ids,
        )
        study = self.storage_service.raw_study_service.import_study(study, stream)
        study.updated_at = datetime.utcnow()

        self._save_study(study, params.user, group_ids)
        self.event_bus.push(
            Event(
                type=EventType.STUDY_CREATED,
                payload=study.to_json_summary(),
                permissions=PermissionInfo.from_study(study),
            )
        )

        logger.info("study %s imported by user %s", study.id, params.get_user_id())
        return str(study.id)

    def import_output(
        self,
        uuid: str,
        output: t.Union[t.BinaryIO, Path],
        params: RequestParameters,
        output_name_suffix: t.Optional[str] = None,
        auto_unzip: bool = True,
    ) -> t.Optional[str]:
        """
        Import specific output simulation inside study
        Args:
            uuid: study uuid
            output: zip file with simulation folder or simulation folder path
            params: request parameters
            output_name_suffix: optional suffix name for the output
            auto_unzip: add a task to unzip the output after import

        Returns: output simulation json formatted

        """
        logger.info(f"Importing new output for study {uuid}")
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.RUN)
        self._assert_study_unarchived(study)
        if not Path(study.path).exists():
            raise StudyNotFoundError(f"Study files were not found for study {uuid}")

        output_id = self.storage_service.get_storage(study).import_output(study, output, output_name_suffix)
        remove_from_cache(cache=self.cache_service, root_id=study.id)
        logger.info("output added to study %s by user %s", uuid, params.get_user_id())

        if output_id and isinstance(output, Path) and output.suffix == ".zip" and auto_unzip:
            self.unarchive_output(uuid, output_id, not is_managed(study), params)

        return output_id

    def _create_edit_study_command(
        self,
        tree_node: INode[JSON, SUB_JSON, JSON],
        url: str,
        data: SUB_JSON,
    ) -> ICommand:
        """
        Create correct command to edit study
        Args:
            tree_node: target node of the command
            url: data path to reach
            data: new data to replace

        Returns: ICommand that replaces the data

        """

        context = self.storage_service.variant_study_service.command_factory.command_context

        if isinstance(tree_node, IniFileNode):
            return UpdateConfig(
                target=url,
                data=data,
                command_context=context,
            )
        elif isinstance(tree_node, InputSeriesMatrix):
            if isinstance(data, bytes):
                # checks if it corresponds to arrow format or if it's a classic file.
                if data[:5].decode("utf-8") == "ARROW":
                    buffer = pa.BufferReader(data)  # type: ignore
                    table = feather.read_table(buffer)
                    df = table.to_pandas()
                    matrix = df.to_numpy()
                else:
                    matrix = np.loadtxt(io.BytesIO(data), delimiter="\t", dtype=np.float64, ndmin=2)
                    matrix = matrix.reshape((1, 0)) if matrix.size == 0 else matrix
                return ReplaceMatrix(
                    target=url,
                    matrix=matrix.tolist(),
                    command_context=context,
                )
            return ReplaceMatrix(
                target=url,
                matrix=data,
                command_context=context,
            )
        elif isinstance(tree_node, RawFileNode):
            if url.split("/")[-1] == "comments":
                return UpdateComments(
                    comments=data,
                    command_context=context,
                )
            elif isinstance(data, bytes):
                return UpdateRawFile(
                    target=url,
                    b64Data=base64.b64encode(data).decode("utf-8"),
                    command_context=context,
                )
        raise NotImplementedError()

    def _edit_study_using_command(
        self,
        study: Study,
        url: str,
        data: SUB_JSON,
        *,
        create_missing: bool = False,
    ) -> ICommand:
        """
        Replace data on disk with new, using variant commands.

        In addition to regular configuration changes, this function also allows the end user
        to store files on disk, in the "user" directory of the study (without using variant commands).

        Args:
            study: study
            url: data path to reach
            data: new data to replace
            create_missing: Flag to indicate whether to create file or parent directories if missing.
        """
        study_service = self.storage_service.get_storage(study)
        file_study = study_service.get_raw(metadata=study)

        file_relpath = PurePosixPath(url.strip().strip("/"))
        file_path = study_service.get_study_path(study).joinpath(file_relpath)
        create_missing &= not file_path.exists()
        if create_missing:
            # IMPORTANT: We prohibit deep file system changes in private directories.
            # - File and directory creation is only possible for the "user" directory,
            #   because the "input" and "output" directories are managed by Antares.
            # - We also prohibit writing files in the "user/expansion" folder which currently
            #   contains the Xpansion tool configuration.
            #   This configuration should be moved to the "input/expansion" directory in the future.
            if file_relpath and file_relpath.parts[0] == "user" and file_relpath.parts[1] != "expansion":
                # In the case of variants, we must write the file directly in the study's snapshot folder,
                # because the "user" folder is not managed by the command mechanism.
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.touch()

        # A 404 Not Found error is raised if the file does not exist.
        tree_node = file_study.tree.get_node(file_relpath.parts)  # type: ignore

        command = self._create_edit_study_command(tree_node=tree_node, url=url, data=data)

        if isinstance(study_service, RawStudyService):
            res = command.apply(study_data=file_study)
            if not is_managed(study):
                tree_node.denormalize()
            if not res.status:
                raise CommandApplicationError(res.message)

            # noinspection SpellCheckingInspection
            url = "study/antares/lastsave"
            last_save_node = file_study.tree.get_node(url.split("/"))
            cmd = self._create_edit_study_command(tree_node=last_save_node, url=url, data=int(time.time()))
            cmd.apply(file_study)

            self.storage_service.variant_study_service.invalidate_cache(study)

        elif isinstance(study_service, VariantStudyService):
            study_service.append_command(
                study_id=file_study.config.study_id,
                command=command.to_dto(),
                params=RequestParameters(user=DEFAULT_ADMIN_USER),
            )

        else:  # pragma: no cover
            raise TypeError(repr(type(study_service)))

        return command  # for testing purpose

    def apply_commands(
        self, uuid: str, commands: t.List[CommandDTO], params: RequestParameters
    ) -> t.Optional[t.List[str]]:
        study = self.get_study(uuid)
        if isinstance(study, VariantStudy):
            return self.storage_service.variant_study_service.append_commands(uuid, commands, params)
        else:
            file_study = self.storage_service.raw_study_service.get_raw(study)
            assert_permission(params.user, study, StudyPermissionType.WRITE)
            self._assert_study_unarchived(study)
            parsed_commands: t.List[ICommand] = []
            for command in commands:
                parsed_commands.extend(self.storage_service.variant_study_service.command_factory.to_command(command))
            execute_or_add_commands(
                study,
                file_study,
                parsed_commands,
                self.storage_service,
            )
        self.event_bus.push(
            Event(
                type=EventType.STUDY_DATA_EDITED,
                payload=study.to_json_summary(),
                permissions=PermissionInfo.from_study(study),
            )
        )
        logger.info(
            "Study %s updated by user %s",
            uuid,
            params.get_user_id(),
        )
        return None

    def edit_study(
        self,
        uuid: str,
        url: str,
        new: SUB_JSON,
        params: RequestParameters,
        *,
        create_missing: bool = False,
    ) -> JSON:
        """
        Replace data inside study.

        Args:
            uuid: study id
            url: path data target in study
            new: new data to replace
            params: request parameters
            create_missing: Flag to indicate whether to create file or parent directories if missing.

        Returns: new data replaced
        """
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.WRITE)
        self._assert_study_unarchived(study)

        self._edit_study_using_command(study=study, url=url.strip().strip("/"), data=new, create_missing=create_missing)

        self.event_bus.push(
            Event(
                type=EventType.STUDY_DATA_EDITED,
                payload=study.to_json_summary(),
                permissions=PermissionInfo.from_study(study),
            )
        )
        logger.info(
            "data %s on study %s updated by user %s",
            url,
            uuid,
            params.get_user_id(),
        )
        return t.cast(JSON, new)

    def change_owner(self, study_id: str, owner_id: int, params: RequestParameters) -> None:
        """
        Change study owner
        Args:
            study_id: study uuid
            owner_id: new owner id
            params: request parameters

        Returns:

        """
        study = self.get_study(study_id)
        assert_permission(params.user, study, StudyPermissionType.MANAGE_PERMISSIONS)
        self._assert_study_unarchived(study)
        new_owner = self.user_service.get_user(owner_id, params)
        study.owner = new_owner
        self.repository.save(study)
        self.event_bus.push(
            Event(
                type=EventType.STUDY_EDITED,
                payload=study.to_json_summary(),
                permissions=PermissionInfo.from_study(study),
            )
        )

        owner_name = None if new_owner is None else new_owner.name
        self._edit_study_using_command(study=study, url="study/antares/author", data=owner_name)

        logger.info(
            "user %s change study %s owner to %d",
            params.get_user_id(),
            study_id,
            owner_id,
        )

    def add_group(self, study_id: str, group_id: str, params: RequestParameters) -> None:
        """
        Attach new group on study.

        Args:
            study_id: study uuid
            group_id: group id to attach
            params: request parameters

        Returns:

        """
        study = self.get_study(study_id)
        assert_permission(params.user, study, StudyPermissionType.MANAGE_PERMISSIONS)
        group = self.user_service.get_group(group_id, params)
        if group not in study.groups:
            study.groups = study.groups + [group]
        self.repository.save(study)
        self.event_bus.push(
            Event(
                type=EventType.STUDY_EDITED,
                payload=study.to_json_summary(),
                permissions=PermissionInfo.from_study(study),
            )
        )

        logger.info(
            "adding group %s to study %s by user %s",
            group_id,
            study_id,
            params.get_user_id(),
        )

    def remove_group(self, study_id: str, group_id: str, params: RequestParameters) -> None:
        """
        Detach group on study
        Args:
            study_id: study uuid
            group_id: group to detach
            params: request parameters

        Returns:

        """
        study = self.get_study(study_id)
        assert_permission(params.user, study, StudyPermissionType.MANAGE_PERMISSIONS)
        study.groups = [group for group in study.groups if group.id != group_id]
        self.repository.save(study)
        self.event_bus.push(
            Event(
                type=EventType.STUDY_EDITED,
                payload=study.to_json_summary(),
                permissions=PermissionInfo.from_study(study),
            )
        )

        logger.info(
            "removing group %s to study %s by user %s",
            group_id,
            study_id,
            params.get_user_id(),
        )

    def set_public_mode(self, study_id: str, mode: PublicMode, params: RequestParameters) -> None:
        """
        Update public mode permission on study
        Args:
            study_id: study uuid
            mode: new public permission
            params: request parameters

        Returns:

        """
        study = self.get_study(study_id)
        assert_permission(params.user, study, StudyPermissionType.MANAGE_PERMISSIONS)
        study.public_mode = mode
        self.repository.save(study)
        self.event_bus.push(
            Event(
                type=EventType.STUDY_EDITED,
                payload=study.to_json_summary(),
                permissions=PermissionInfo.from_study(study),
            )
        )
        logger.info(
            "updated public mode of study %s by user %s",
            study_id,
            params.get_user_id(),
        )

    def check_errors(self, uuid: str) -> t.List[str]:
        study = self.get_study(uuid)
        self._assert_study_unarchived(study)
        return self.storage_service.raw_study_service.check_errors(study)

    def get_all_areas(
        self,
        uuid: str,
        area_type: t.Optional[AreaType],
        ui: bool,
        params: RequestParameters,
    ) -> t.Union[t.List[AreaInfoDTO], t.Dict[str, t.Any]]:
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.READ)
        return self.areas.get_all_areas_ui_info(study) if ui else self.areas.get_all_areas(study, area_type)

    def get_all_links(
        self,
        uuid: str,
        with_ui: bool,
        params: RequestParameters,
    ) -> t.List[LinkInfoDTO]:
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.READ)
        return self.links.get_all_links(study, with_ui)

    def create_area(
        self,
        uuid: str,
        area_creation_dto: AreaCreationDTO,
        params: RequestParameters,
    ) -> AreaInfoDTO:
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.WRITE)
        self._assert_study_unarchived(study)
        new_area = self.areas.create_area(study, area_creation_dto)
        self.event_bus.push(
            Event(
                type=EventType.STUDY_DATA_EDITED,
                payload=study.to_json_summary(),
                permissions=PermissionInfo.from_study(study),
            )
        )
        return new_area

    def create_link(
        self,
        uuid: str,
        link_creation_dto: LinkInfoDTO,
        params: RequestParameters,
    ) -> LinkInfoDTO:
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.WRITE)
        self._assert_study_unarchived(study)
        new_link = self.links.create_link(study, link_creation_dto)
        self.event_bus.push(
            Event(
                type=EventType.STUDY_DATA_EDITED,
                payload=study.to_json_summary(),
                permissions=PermissionInfo.from_study(study),
            )
        )
        return new_link

    def update_area(
        self,
        uuid: str,
        area_id: str,
        area_patch_dto: PatchArea,
        params: RequestParameters,
    ) -> AreaInfoDTO:
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.WRITE)
        self._assert_study_unarchived(study)
        updated_area = self.areas.update_area_metadata(study, area_id, area_patch_dto)
        self.event_bus.push(
            Event(
                type=EventType.STUDY_DATA_EDITED,
                payload=study.to_json_summary(),
                permissions=PermissionInfo.from_study(study),
            )
        )
        return updated_area

    def update_area_ui(
        self,
        uuid: str,
        area_id: str,
        area_ui: UpdateAreaUi,
        layer: str,
        params: RequestParameters,
    ) -> None:
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.WRITE)
        self._assert_study_unarchived(study)
        return self.areas.update_area_ui(study, area_id, area_ui, layer)

    def update_thermal_cluster_metadata(
        self,
        uuid: str,
        area_id: str,
        clusters_metadata: t.Dict[str, PatchCluster],
        params: RequestParameters,
    ) -> AreaInfoDTO:
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.WRITE)
        self._assert_study_unarchived(study)
        return self.areas.update_thermal_cluster_metadata(study, area_id, clusters_metadata)

    def delete_area(self, uuid: str, area_id: str, params: RequestParameters) -> None:
        """
        Delete area from study if it is not referenced by a binding constraint,
        otherwise raise an HTTP 403 Forbidden error.

        Args:
            uuid: The study ID.
            area_id: The area ID to delete.
            params: The request parameters used to check user permissions.

        Raises:
            ReferencedObjectDeletionNotAllowed: If the area is referenced by a binding constraint.
        """
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.WRITE)
        self._assert_study_unarchived(study)
        referencing_binding_constraints = self.binding_constraint_manager.get_binding_constraints(
            study, ConstraintFilters(area_name=area_id)
        )
        if referencing_binding_constraints:
            binding_ids = [bc.id for bc in referencing_binding_constraints]
            raise ReferencedObjectDeletionNotAllowed(area_id, binding_ids, object_type="Area")
        self.areas.delete_area(study, area_id)
        self.event_bus.push(
            Event(
                type=EventType.STUDY_DATA_EDITED,
                payload=study.to_json_summary(),
                permissions=PermissionInfo.from_study(study),
            )
        )

    def delete_link(
        self,
        uuid: str,
        area_from: str,
        area_to: str,
        params: RequestParameters,
    ) -> None:
        """
        Delete link from study if it is not referenced by a binding constraint,
        otherwise raise an HTTP 403 Forbidden error.

        Args:
            uuid: The study ID.
            area_from: The area from which the link starts.
            area_to: The area to which the link ends.
            params: The request parameters used to check user permissions.

        Raises:
            ReferencedObjectDeletionNotAllowed: If the link is referenced by a binding constraint.
        """
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.WRITE)
        self._assert_study_unarchived(study)
        link_id = LinkTerm(area1=area_from, area2=area_to).generate_id()
        referencing_binding_constraints = self.binding_constraint_manager.get_binding_constraints(
            study, ConstraintFilters(link_id=link_id)
        )
        if referencing_binding_constraints:
            binding_ids = [bc.id for bc in referencing_binding_constraints]
            raise ReferencedObjectDeletionNotAllowed(link_id, binding_ids, object_type="Link")
        self.links.delete_link(study, area_from, area_to)
        self.event_bus.push(
            Event(
                type=EventType.STUDY_DATA_EDITED,
                payload=study.to_json_summary(),
                permissions=PermissionInfo.from_study(study),
            )
        )

    def archive(self, uuid: str, params: RequestParameters) -> str:
        logger.info(f"Archiving study {uuid}")
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.WRITE)

        self._assert_study_unarchived(study)

        if not isinstance(study, RawStudy):
            raise StudyTypeUnsupported(study.id, study.type)

        if not is_managed(study):
            raise NotAManagedStudyException(study.id)

        if self.task_service.list_tasks(
            TaskListFilter(
                ref_id=uuid,
                type=[TaskType.ARCHIVE, TaskType.UNARCHIVE],
                status=[TaskStatus.RUNNING, TaskStatus.PENDING],
            ),
            RequestParameters(user=DEFAULT_ADMIN_USER),
        ):
            raise TaskAlreadyRunning()

        def archive_task(notifier: TaskUpdateNotifier) -> TaskResult:
            study_to_archive = self.get_study(uuid)
            self.storage_service.raw_study_service.archive(study_to_archive)
            study_to_archive.archived = True
            self.repository.save(study_to_archive)
            self.event_bus.push(
                Event(
                    type=EventType.STUDY_EDITED,
                    payload=study_to_archive.to_json_summary(),
                    permissions=PermissionInfo.from_study(study_to_archive),
                )
            )
            return TaskResult(success=True, message="ok")

        return self.task_service.add_task(
            archive_task,
            f"Study {study.name} archiving",
            task_type=TaskType.ARCHIVE,
            ref_id=study.id,
            custom_event_messages=None,
            request_params=params,
        )

    def unarchive(self, uuid: str, params: RequestParameters) -> str:
        study = self.get_study(uuid)
        if not study.archived:
            raise HTTPException(http.HTTPStatus.BAD_REQUEST, "Study is not archived")

        if self.task_service.list_tasks(
            TaskListFilter(
                ref_id=uuid,
                type=[TaskType.UNARCHIVE, TaskType.ARCHIVE],
                status=[TaskStatus.RUNNING, TaskStatus.PENDING],
            ),
            RequestParameters(user=DEFAULT_ADMIN_USER),
        ):
            raise TaskAlreadyRunning()

        assert_permission(params.user, study, StudyPermissionType.WRITE)

        if not isinstance(study, RawStudy):
            raise StudyTypeUnsupported(study.id, study.type)

        def unarchive_task(notifier: TaskUpdateNotifier) -> TaskResult:
            study_to_archive = self.get_study(uuid)
            self.storage_service.raw_study_service.unarchive(study_to_archive)
            study_to_archive.archived = False

            os.unlink(self.storage_service.raw_study_service.get_archive_path(study_to_archive))
            self.repository.save(study_to_archive)
            self.event_bus.push(
                Event(
                    type=EventType.STUDY_EDITED,
                    payload=study.to_json_summary(),
                    permissions=PermissionInfo.from_study(study),
                )
            )
            remove_from_cache(cache=self.cache_service, root_id=uuid)
            return TaskResult(success=True, message="ok")

        return self.task_service.add_task(
            unarchive_task,
            f"Study {study.name} unarchiving",
            task_type=TaskType.UNARCHIVE,
            ref_id=study.id,
            custom_event_messages=None,
            request_params=params,
        )

    def _save_study(
        self,
        study: Study,
        owner: t.Optional[JWTUser] = None,
        group_ids: t.Sequence[str] = (),
    ) -> None:
        """
        Create or update a study with specified attributes.

        This function is responsible for creating a new study or updating an existing one
        with the provided information.

        Args:
            study: The study to be saved or updated.
            owner: The owner of the study (current authenticated user).
            group_ids: The list of group IDs to associate with the study.

        Raises:
            UserHasNotPermissionError:
                If the owner or the group role is not specified.
        """
        if not owner:
            raise UserHasNotPermissionError("owner is not specified or has invalid authentication")

        if isinstance(study, RawStudy):
            study.content_status = StudyContentStatus.VALID

        study.owner = self.user_service.get_user(owner.impersonator, params=RequestParameters(user=owner))

        study.groups.clear()
        for gid in group_ids:
            owned_groups = (g for g in owner.groups if g.id == gid)
            jwt_group: t.Optional[JWTGroup] = next(owned_groups, None)
            if jwt_group is None or jwt_group.role is None:
                raise UserHasNotPermissionError(f"Permission denied for group ID: {gid}")
            study.groups.append(Group(id=jwt_group.id, name=jwt_group.name))

        self.repository.save(study)

    def get_study(self, uuid: str) -> Study:
        """
        Get study information
        Args:
            uuid: study uuid

        Returns: study information

        """

        study = self.repository.get(uuid)
        if not study:
            sanitized = str(escape(uuid))
            logger.warning(
                "Study %s not found in metadata db",
                sanitized,
            )
            raise StudyNotFoundError(uuid)
        return study

    def _assert_study_unarchived(self, study: Study, raise_exception: bool = True) -> bool:
        if study.archived and raise_exception:
            raise UnsupportedOperationOnArchivedStudy(study.id)
        return not study.archived

    def _analyse_study(self, metadata: Study) -> StudyContentStatus:
        """
        Analyzes the integrity of a study.

        Args:
            metadata: The study to analyze.

        Returns:
            - VALID if the study has no integrity issues.
            - WARNING if the study has some issues.
            - ERROR if the tree was unable to analyze the structure without raising an error.
        """
        try:
            if not isinstance(metadata, RawStudy):
                raise StudyTypeUnsupported(metadata.id, metadata.type)

            if self.storage_service.raw_study_service.check_errors(metadata):
                return StudyContentStatus.WARNING
            else:
                return StudyContentStatus.VALID
        except Exception as e:
            logger.error(e)
            return StudyContentStatus.ERROR

    # noinspection PyUnusedLocal
    @staticmethod
    def get_studies_versions(params: RequestParameters) -> t.List[str]:
        return list(STUDY_REFERENCE_TEMPLATES)

    def create_xpansion_configuration(
        self,
        uuid: str,
        zipped_config: t.Optional[UploadFile],
        params: RequestParameters,
    ) -> None:
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.WRITE)
        self._assert_study_unarchived(study)
        self.xpansion_manager.create_xpansion_configuration(study, zipped_config)

    def delete_xpansion_configuration(self, uuid: str, params: RequestParameters) -> None:
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.WRITE)
        self._assert_study_unarchived(study)
        self.xpansion_manager.delete_xpansion_configuration(study)

    def get_xpansion_settings(self, uuid: str, params: RequestParameters) -> GetXpansionSettings:
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.READ)
        return self.xpansion_manager.get_xpansion_settings(study)

    def update_xpansion_settings(
        self,
        uuid: str,
        xpansion_settings_dto: UpdateXpansionSettings,
        params: RequestParameters,
    ) -> GetXpansionSettings:
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.READ)
        self._assert_study_unarchived(study)
        return self.xpansion_manager.update_xpansion_settings(study, xpansion_settings_dto)

    def add_candidate(
        self,
        uuid: str,
        xpansion_candidate_dto: XpansionCandidateDTO,
        params: RequestParameters,
    ) -> XpansionCandidateDTO:
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.WRITE)
        self._assert_study_unarchived(study)
        return self.xpansion_manager.add_candidate(study, xpansion_candidate_dto)

    def get_candidate(self, uuid: str, candidate_name: str, params: RequestParameters) -> XpansionCandidateDTO:
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.READ)
        return self.xpansion_manager.get_candidate(study, candidate_name)

    def get_candidates(self, uuid: str, params: RequestParameters) -> t.List[XpansionCandidateDTO]:
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.READ)
        return self.xpansion_manager.get_candidates(study)

    def update_xpansion_candidate(
        self,
        uuid: str,
        candidate_name: str,
        xpansion_candidate_dto: XpansionCandidateDTO,
        params: RequestParameters,
    ) -> None:
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.READ)
        self._assert_study_unarchived(study)
        return self.xpansion_manager.update_candidate(study, candidate_name, xpansion_candidate_dto)

    def delete_xpansion_candidate(self, uuid: str, candidate_name: str, params: RequestParameters) -> None:
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.READ)
        self._assert_study_unarchived(study)
        return self.xpansion_manager.delete_candidate(study, candidate_name)

    def update_xpansion_constraints_settings(
        self,
        uuid: str,
        constraints_file_name: str,
        params: RequestParameters,
    ) -> GetXpansionSettings:
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.WRITE)
        self._assert_study_unarchived(study)
        return self.xpansion_manager.update_xpansion_constraints_settings(study, constraints_file_name)

    def update_matrix(
        self,
        uuid: str,
        path: str,
        matrix_edit_instruction: t.List[MatrixEditInstruction],
        params: RequestParameters,
    ) -> None:
        """
        Updates a matrix in a study based on the provided edit instructions.

        Args:
            uuid: The UUID of the study.
            path: The path of the matrix to update.
            matrix_edit_instruction: A list of edit instructions to be applied to the matrix.
            params: Additional request parameters.

        Raises:
            BadEditInstructionException: If an error occurs while updating the matrix.

        Permissions:
            - User must have WRITE permission on the study.
        """
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.WRITE)
        self._assert_study_unarchived(study)
        try:
            self.matrix_manager.update_matrix(study, path, matrix_edit_instruction)
        except MatrixManagerError as exc:
            raise BadEditInstructionException(str(exc)) from exc

    def check_and_update_all_study_versions_in_database(self, params: RequestParameters) -> None:
        """
        This function updates studies version on the db.

        **Warnings: Only users with Admins rights should be able to run this function.**

        Args:
            params: Request parameters holding user ID and groups

        Raises:
            UserHasNotPermissionError: if params user is not admin.

        """
        if params.user and not params.user.is_site_admin():
            logger.error(f"User {params.user.id} is not site admin")
            raise UserHasNotPermissionError()
        studies = self.repository.get_all(
            study_filter=StudyFilter(managed=False, access_permissions=AccessPermissions.from_params(params))
        )

        for study in studies:
            storage = self.storage_service.raw_study_service
            storage.check_and_update_study_version_in_database(study)

    def archive_outputs(self, study_id: str, params: RequestParameters) -> None:
        logger.info(f"Archiving all outputs for study {study_id}")
        study = self.get_study(study_id)
        assert_permission(params.user, study, StudyPermissionType.WRITE)
        self._assert_study_unarchived(study)
        study = self.get_study(study_id)
        file_study = self.storage_service.get_storage(study).get_raw(study)
        for output in file_study.config.outputs:
            if not file_study.config.outputs[output].archived:
                self.archive_output(study_id, output, params)

    @staticmethod
    def _get_output_archive_task_names(study: Study, output_id: str) -> t.Tuple[str, str]:
        return (
            f"Archive output {study.id}/{output_id}",
            f"Unarchive output {study.name}/{output_id} ({study.id})",
        )

    def archive_output(
        self,
        study_id: str,
        output_id: str,
        params: RequestParameters,
        force: bool = False,
    ) -> t.Optional[str]:
        study = self.get_study(study_id)
        assert_permission(params.user, study, StudyPermissionType.WRITE)
        self._assert_study_unarchived(study)

        archive_task_names = StudyService._get_output_archive_task_names(study, output_id)
        task_name = archive_task_names[0]

        if not force:
            study_tasks = self.task_service.list_tasks(
                TaskListFilter(
                    ref_id=study_id,
                    name=task_name,
                    type=[TaskType.UNARCHIVE, TaskType.ARCHIVE],
                    status=[TaskStatus.RUNNING, TaskStatus.PENDING],
                ),
                RequestParameters(user=DEFAULT_ADMIN_USER),
            )
            if len(list(filter(lambda t: t.name in archive_task_names, study_tasks))):
                raise TaskAlreadyRunning()

        def archive_output_task(
            notifier: TaskUpdateNotifier,
        ) -> TaskResult:
            try:
                study = self.get_study(study_id)
                stopwatch = StopWatch()
                self.storage_service.get_storage(study).archive_study_output(study, output_id)
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

        task_id = self.task_service.add_task(
            archive_output_task,
            task_name,
            task_type=TaskType.ARCHIVE,
            ref_id=study.id,
            custom_event_messages=None,
            request_params=params,
        )

        return task_id

    def unarchive_output(
        self,
        study_id: str,
        output_id: str,
        keep_src_zip: bool,
        params: RequestParameters,
    ) -> t.Optional[str]:
        study = self.get_study(study_id)
        assert_permission(params.user, study, StudyPermissionType.READ)
        self._assert_study_unarchived(study)

        archive_task_names = StudyService._get_output_archive_task_names(study, output_id)
        task_name = archive_task_names[1]

        study_tasks = self.task_service.list_tasks(
            TaskListFilter(
                ref_id=study_id,
                type=[TaskType.UNARCHIVE, TaskType.ARCHIVE],
                status=[TaskStatus.RUNNING, TaskStatus.PENDING],
            ),
            RequestParameters(user=DEFAULT_ADMIN_USER),
        )
        if len(list(filter(lambda t: t.name in archive_task_names, study_tasks))):
            raise TaskAlreadyRunning()

        def unarchive_output_task(
            notifier: TaskUpdateNotifier,
        ) -> TaskResult:
            try:
                study = self.get_study(study_id)
                stopwatch = StopWatch()
                self.storage_service.get_storage(study).unarchive_study_output(study, output_id, keep_src_zip)
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

        task_id: t.Optional[str] = None
        workspace = getattr(study, "workspace", DEFAULT_WORKSPACE_NAME)
        if workspace != DEFAULT_WORKSPACE_NAME:
            dest = Path(study.path) / "output" / output_id
            src = Path(study.path) / "output" / f"{output_id}.zip"
            task_id = self.task_service.add_worker_task(
                TaskType.UNARCHIVE,
                f"unarchive_{workspace}",
                ArchiveTaskArgs(
                    src=str(src),
                    dest=str(dest),
                    remove_src=not keep_src_zip,
                ).dict(),
                name=task_name,
                ref_id=study.id,
                request_params=params,
            )

        if not task_id:
            task_id = self.task_service.add_task(
                unarchive_output_task,
                task_name,
                task_type=TaskType.UNARCHIVE,
                ref_id=study.id,
                custom_event_messages=None,
                request_params=params,
            )

        return task_id

    def generate_timeseries(self, study: Study, params: RequestParameters) -> str:
        task_name = f"Generating thermal timeseries for study {study.name} ({study.id})"
        study_tasks = self.task_service.list_tasks(
            TaskListFilter(
                ref_id=study.id,
                type=[TaskType.THERMAL_CLUSTER_SERIES_GENERATION],
                status=[TaskStatus.RUNNING, TaskStatus.PENDING],
            ),
            RequestParameters(user=DEFAULT_ADMIN_USER),
        )
        if len(study_tasks) > 0:
            raise TaskAlreadyRunning()

        thermal_cluster_timeseries_generation_task = ThermalClusterTimeSeriesGeneratorTask(
            study.id,
            repository=self.repository,
            storage_service=self.storage_service,
            event_bus=self.event_bus,
        )

        return self.task_service.add_task(
            thermal_cluster_timeseries_generation_task,
            task_name,
            task_type=TaskType.THERMAL_CLUSTER_SERIES_GENERATION,
            ref_id=study.id,
            custom_event_messages=None,
            request_params=params,
        )

    def upgrade_study(
        self,
        study_id: str,
        target_version: str,
        params: RequestParameters,
    ) -> str:
        study = self.get_study(study_id)
        assert_permission(params.user, study, StudyPermissionType.WRITE)
        self._assert_study_unarchived(study)

        # The upgrade of a study variant requires the use of a command specifically dedicated to the upgrade.
        # However, such a command does not currently exist. Moreover, upgrading a study (whether raw or variant)
        # directly impacts its descendants, as it would necessitate upgrading all of them.
        # It’s uncertain whether this would be an acceptable behavior.
        # For this reason, upgrading a study is not possible if the study is a variant or if it has descendants.

        # First check if the study is a variant study, if so throw an error
        if isinstance(study, VariantStudy):
            raise StudyVariantUpgradeError(True)
        # If the study is a parent raw study and has variants, throw an error
        elif self.repository.has_children(study_id):
            raise StudyVariantUpgradeError(False)

        # Checks versions coherence before launching the task
        if not target_version:
            target_version = find_next_version(study.version)
        else:
            check_versions_coherence(study.version, target_version)

        task_name = f"Upgrade study {study.name} ({study.id}) to version {target_version}"
        study_tasks = self.task_service.list_tasks(
            TaskListFilter(
                ref_id=study_id,
                type=[TaskType.UPGRADE_STUDY],
                status=[TaskStatus.RUNNING, TaskStatus.PENDING],
            ),
            RequestParameters(user=DEFAULT_ADMIN_USER),
        )
        if len(study_tasks) > 0:
            raise TaskAlreadyRunning()

        study_upgrader_task = StudyUpgraderTask(
            study_id,
            target_version,
            repository=self.repository,
            storage_service=self.storage_service,
            cache_service=self.cache_service,
            event_bus=self.event_bus,
        )

        return self.task_service.add_task(
            study_upgrader_task,
            task_name,
            task_type=TaskType.UPGRADE_STUDY,
            ref_id=study.id,
            custom_event_messages=None,
            request_params=params,
        )

    def get_disk_usage(self, uuid: str, params: RequestParameters) -> int:
        """
        Calculates the size of the disk used to store the study if the user has permissions.

        The calculation of disk space concerns the entire study directory.
        In the case of a variant, the snapshot folder must be taken into account, as well as the outputs.

        Args:
            uuid: the study ID.
            params: user request parameters.

        Returns:
            Disk usage of the study in bytes.

        Raises:
            UserHasNotPermissionError: If the user does not have the READ permissions (HTTP status 403).
        """
        study = self.get_study(uuid=uuid)
        assert_permission(params.user, study, StudyPermissionType.READ)
        study_path = self.storage_service.raw_study_service.get_study_path(study)
        # If the study is a variant, it's possible that it only exists in DB and not on disk. If so, we return 0.
        return get_disk_usage(study_path) if study_path.exists() else 0

    def get_matrix_with_index_and_header(
        self,
        *,
        study_id: str,
        path: str,
        with_index: bool,
        with_header: bool,
        parameters: RequestParameters,
    ) -> pd.DataFrame:
        """
        Retrieves a matrix from a study with the option to include the index and header.

        Args:
            study_id: The UUID of the study from which to retrieve the matrix.
            path: The relative path to the matrix within the study.
            with_index: A boolean indicating whether to include the index in the retrieved matrix.
            with_header: A boolean indicating whether to include the header in the retrieved matrix.
            parameters: The request parameters, including the user information.

        Returns:
            A DataFrame representing the matrix.

        Raises:
            HTTPException: If the matrix does not exist or the user does not have the necessary permissions.
        """

        matrix_path = Path(path)
        study = self.get_study(study_id)

        if matrix_path.parts in [("input", "hydro", "allocation"), ("input", "hydro", "correlation")]:
            all_areas = t.cast(
                t.List[AreaInfoDTO],
                self.get_all_areas(study_id, area_type=AreaType.AREA, ui=False, params=parameters),
            )
            if matrix_path.parts[-1] == "allocation":
                hydro_matrix = self.allocation_manager.get_allocation_matrix(study, all_areas)
            else:
                hydro_matrix = self.correlation_manager.get_correlation_matrix(all_areas, study, [])  # type: ignore
            return pd.DataFrame(data=hydro_matrix.data, columns=hydro_matrix.columns, index=hydro_matrix.index)

        matrix_obj = self.get(study_id, path, depth=3, format="json", params=parameters)
        if set(matrix_obj) != {"data", "index", "columns"}:
            raise IncorrectPathError(f"The provided path does not point to a valid matrix: '{path}'")
        if not matrix_obj["data"]:
            return pd.DataFrame()

        df_matrix = pd.DataFrame(**matrix_obj)
        if with_index:
            matrix_index = self.get_input_matrix_startdate(study_id, path, parameters)
            time_column = pd.date_range(
                start=matrix_index.start_date, periods=len(df_matrix), freq=matrix_index.level.value[0]
            )
            df_matrix.index = time_column

        adjust_matrix_columns_index(
            df_matrix,
            path,
            with_index=with_index,
            with_header=with_header,
            study_version=int(study.version),
        )

        return df_matrix

    def asserts_no_thermal_in_binding_constraints(
        self, study: Study, area_id: str, cluster_ids: t.Sequence[str]
    ) -> None:
        """
        Check that no cluster is referenced in a binding constraint, otherwise raise an HTTP 403 Forbidden error.

        Args:
            study: input study for which an update is to be committed
            area_id: area ID to be checked
            cluster_ids: IDs of the thermal clusters to be checked

        Raises:
            ReferencedObjectDeletionNotAllowed: if a cluster is referenced in a binding constraint
        """

        for cluster_id in cluster_ids:
            ref_bcs = self.binding_constraint_manager.get_binding_constraints(
                study, ConstraintFilters(cluster_id=f"{area_id}.{cluster_id}")
            )
            if ref_bcs:
                binding_ids = [bc.id for bc in ref_bcs]
                raise ReferencedObjectDeletionNotAllowed(cluster_id, binding_ids, object_type="Cluster")
