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
import base64
import collections
import contextlib
import http
import io
import logging
import os
import shutil
from datetime import timedelta
from pathlib import Path, PurePosixPath
from typing import Any, BinaryIO, Callable, Dict, List, Optional, Sequence, Type, cast
from uuid import uuid4

import pandas as pd
from antares.study.version import StudyVersion
from fastapi import HTTPException
from markupsafe import escape
from typing_extensions import override

from antarest.core.config import Config
from antarest.core.exceptions import (
    BadEditInstructionException,
    ChildNotFoundError,
    CommandApplicationError,
    IncorrectArgumentsForCopy,
    IncorrectPathError,
    MatrixImportFailed,
    NotAManagedStudyException,
    ReferencedObjectDeletionNotAllowed,
    ResourceCreationNotAllowed,
    ResourceDeletionNotAllowed,
    StudyDeletionNotAllowed,
    StudyNotFoundError,
    StudyVariantUpgradeError,
    TaskAlreadyRunning,
    UnsupportedOperationOnArchivedStudy,
    UnsupportedOperationOnThisStudyType,
)
from antarest.core.filetransfer.model import FileDownloadTaskDTO
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.interfaces.cache import ICache, study_raw_cache_key, update_cache
from antarest.core.interfaces.eventbus import Event, EventType, IEventBus
from antarest.core.jwt import JWTGroup
from antarest.core.model import JSON, SUB_JSON, PermissionInfo, PublicMode, StudyPermissionType
from antarest.core.requests import UserHasNotPermissionError
from antarest.core.serde.ini_reader import IniReader
from antarest.core.tasks.model import TaskListFilter, TaskResult, TaskStatus, TaskType
from antarest.core.tasks.service import ITaskNotifier, ITaskService, NoopNotifier
from antarest.core.utils.archives import ArchiveFormat, is_archive_format
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import StopWatch, current_time
from antarest.launcher.repository import JobResultRepository
from antarest.login.model import Group
from antarest.login.service import LoginService
from antarest.login.utils import get_current_user, get_user_id, get_user_impersonator
from antarest.matrixstore.matrix_editor import MatrixEditInstruction
from antarest.study.business.adequacy_patch_management import AdequacyPatchManager
from antarest.study.business.advanced_parameters_management import AdvancedParamsManager
from antarest.study.business.allocation_management import AllocationManager
from antarest.study.business.area_management import AreaManager
from antarest.study.business.areas.hydro_management import HydroManager
from antarest.study.business.areas.renewable_management import RenewableManager
from antarest.study.business.areas.st_storage_management import STStorageManager
from antarest.study.business.areas.thermal_management import ThermalManager
from antarest.study.business.binding_constraint_management import BindingConstraintManager, ConstraintFilters
from antarest.study.business.compatibility_parameters_management import CompatibilityParamsManager
from antarest.study.business.correlation_management import CorrelationManager
from antarest.study.business.district_manager import DistrictManager
from antarest.study.business.general_management import GeneralManager
from antarest.study.business.layer_management import LayerManager
from antarest.study.business.link_management import LinkManager
from antarest.study.business.matrix_management import MatrixManager, MatrixManagerError
from antarest.study.business.model.area_model import AreaCreation, AreaInfo, AreaUIData, AreaUIUpdate
from antarest.study.business.model.binding_constraint_model import LinkTerm
from antarest.study.business.model.hydro_allocation_model import HydroAllocationMatrix
from antarest.study.business.model.hydro_correlation_model import HydroCorrelationMatrix
from antarest.study.business.model.link_model import Link, LinkUpdate
from antarest.study.business.model.study_data_model import StudyDataDTO
from antarest.study.business.model.user_model import ResourceType, UserResourceDataCreation, UserResourceDataRemoval
from antarest.study.business.model.xpansion_model import (
    XpansionCandidate,
    XpansionCandidateCreation,
    XpansionResourceFileType,
    XpansionSettings,
    XpansionSettingsUpdate,
)
from antarest.study.business.optimization_management import OptimizationManager
from antarest.study.business.playlist_management import PlaylistManager
from antarest.study.business.scenario_builder_management import ScenarioBuilderManager
from antarest.study.business.study_interface import StudyInterface
from antarest.study.business.table_mode_management import TableModeManager
from antarest.study.business.thematic_trimming_management import ThematicTrimmingManager
from antarest.study.business.timeseries_config_management import TimeSeriesConfigManager
from antarest.study.business.xpansion_management import (
    XpansionManager,
)
from antarest.study.dao.api.study_dao import ReadOnlyStudyDao, StudyDao
from antarest.study.dao.api.study_factory_dao import StudyFactoryDao
from antarest.study.dao.database.database_matrices_provider import StudyDatabaseMatrixUsageProvider
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.dao.database.database_study_factory_dao import DatabaseStudyDaoFactory
from antarest.study.dao.file.file_study_dao import FileStudyTreeDao
from antarest.study.dao.file.file_study_factory_dao import FileStudyDaoFactory
from antarest.study.dao.study_conversion.study_converter import StudyConverter
from antarest.study.directory_service import DirectoryService
from antarest.study.model import (
    DEFAULT_WORKSPACE_NAME,
    NEW_DEFAULT_STUDY_VERSION,
    STUDY_REFERENCE_TEMPLATES,
    MatrixFrequency,
    MatrixIndex,
    RawStudy,
    StorageMode,
    Study,
    StudyContentStatus,
    StudyFolder,
    StudyMetadataDTO,
    StudyMetadataPatchDTO,
)
from antarest.study.repository import (
    StudyFilter,
    StudyMetadataRepository,
    StudyPagination,
    StudySortBy,
)
from antarest.study.storage.matrix_profile import adjust_matrix_columns_index
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfigDTO
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode
from antarest.study.storage.rawstudy.model.filesystem.inode import INode, OriginalFile
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixNode, imports_matrix_from_bytes
from antarest.study.storage.rawstudy.model.filesystem.matrix.output_series_matrix import OutputSeriesMatrix
from antarest.study.storage.rawstudy.model.filesystem.raw_file_node import RawFileNode
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.mcall.synthesis import OutputSynthesis
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.study_upgrader import StudyUpgrader, check_versions_coherence, find_next_version
from antarest.study.storage.utils import (
    assert_permission,
    create_new_empty_study,
    get_start_date,
    is_managed,
    is_study_folder,
    remove_from_cache,
)
from antarest.study.storage.variantstudy.business.utils import transform_command_to_dto
from antarest.study.storage.variantstudy.model.command.generate_thermal_cluster_timeseries import (
    GenerateThermalClusterTimeSeries,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.remove_user_resource import (
    RemoveUserResource,
)
from antarest.study.storage.variantstudy.model.command.replace_comments import ReplaceComments
from antarest.study.storage.variantstudy.model.command.replace_matrix import ReplaceMatrix
from antarest.study.storage.variantstudy.model.command.replace_user_resource import (
    ReplaceUserResource,
)
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig
from antarest.study.storage.variantstudy.model.command.update_raw_file import UpdateRawFile
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy
from antarest.study.storage.variantstudy.model.model import CommandDTO
from antarest.study.storage.variantstudy.variant_study_service import VariantStudyService

logger = logging.getLogger(__name__)

MAX_MISSING_STUDY_TIMEOUT = 2  # days


def get_disk_usage(path: str | Path) -> int:
    """Calculate the total disk usage (in bytes) of a study in a compressed file or directory."""
    path = Path(path)
    if is_archive_format(path.suffix.lower()):
        return os.path.getsize(path)
    total_size = 0
    with contextlib.suppress(FileNotFoundError, PermissionError):
        with os.scandir(path) as it:
            for entry in it:
                with contextlib.suppress(FileNotFoundError, PermissionError):
                    if entry.is_file():
                        total_size += entry.stat().st_size
                    elif entry.is_dir():
                        total_size += get_disk_usage(path=str(entry.path))
    return total_size


def _get_path_inside_user_folder(
    path: str, exception_class: Type[ResourceCreationNotAllowed | ResourceDeletionNotAllowed]
) -> str:
    """
    Retrieves the path inside the `user` folder for a given user path

    Raises exception_class if the path is not located inside the `user` folder
    """
    url = [item for item in path.split("/") if item]
    if len(url) < 2 or url[0] != "user":
        raise exception_class(f"the given path isn't inside the 'User' folder: {path}")
    if url[1] == "expansion":
        raise exception_class(f"the given path is inside the `expansion` folder: {path}")
    return "/".join(url[1:])


def assert_raw(study: Study) -> RawStudy:
    if not isinstance(study, RawStudy):
        raise TypeError("Study must be a RawStudy")
    return study


class TaskProgressRecorder(ICommandListener):
    def __init__(self, notifier: ITaskNotifier) -> None:
        self.notifier = notifier

    @override
    def notify_progress(self, progress: int) -> None:
        return self.notifier.notify_progress(progress)


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
        study_interface_supplier: Callable[[Study], StudyInterface],
        thermal_outage_details: bool,
    ):
        self._study_id = _study_id
        self.repository = repository
        self.storage_service = storage_service
        self.event_bus = event_bus
        self.study_interface_supplier = study_interface_supplier
        self.thermal_outage_details = thermal_outage_details

    def _generate_timeseries(self, notifier: ITaskNotifier) -> None:
        """Run the task (lock the database)."""
        command_context = self.storage_service.variant_study_service.command_factory.command_context
        listener = TaskProgressRecorder(notifier=notifier)
        with db():
            study = self.repository.one(self._study_id)
            study_version = StudyVersion.parse(study.version)
            command = GenerateThermalClusterTimeSeries(
                command_context=command_context,
                study_version=study_version,
                thermal_outage_details=self.thermal_outage_details,
            )
            self.study_interface_supplier(study).add_commands([command], listener)

            if isinstance(study, VariantStudy):
                # In this case we only added the command to the list.
                # It means the generation will really be executed in the next snapshot generation.
                # We don't want this, we want this task to generate the matrices no matter the study.
                # Therefore, we have to launch a variant generation task inside the timeseries generation one.
                variant_service = self.storage_service.variant_study_service
                task_service = variant_service.task_service
                generation_task_id = variant_service.generate_task(study, True, False, listener)
                task_service.await_task(generation_task_id)
                result = task_service.status_task(generation_task_id)
                assert result.result is not None
                if not result.result.success:
                    raise ValueError(result.result.message)

            self.event_bus.push(
                Event(
                    type=EventType.STUDY_EDITED,
                    payload=study.to_json_summary(),
                    permissions=PermissionInfo.from_study(study),
                )
            )

    def run_task(self, notifier: ITaskNotifier) -> TaskResult:
        msg = f"Generating thermal timeseries for study '{self._study_id}'"
        notifier.notify_message(msg)
        self._generate_timeseries(notifier)
        msg = f"Successfully generated thermal timeseries for study '{self._study_id}'"
        notifier.notify_message(msg)
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
        target_version: StudyVersion,
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
        target_version = self._target_version
        is_study_denormalized = False
        with db():
            study_to_upgrade = self.repository.one(study_id)
            try:
                # sourcery skip: extract-method
                study_path = Path(study_to_upgrade.path)
                study_upgrader = StudyUpgrader(study_path, target_version)
                if is_managed(study_to_upgrade) and study_upgrader.should_denormalize_study():
                    # We have to denormalize the study because the upgrade impacts study matrices
                    self.storage_service.raw_study_service.denormalize_study(study_to_upgrade)
                    is_study_denormalized = True
                study_upgrader.upgrade()
                remove_from_cache(self.cache_service, study_to_upgrade.id)
                study_to_upgrade.version = f"{target_version:2d}"
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
                    self.storage_service.raw_study_service.normalize_study(study_to_upgrade)

    def run_task(self, notifier: ITaskNotifier) -> TaskResult:
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
        notifier.notify_message(msg)
        self._upgrade_study()
        msg = f"Successfully upgraded study '{self._study_id}' to version {self._target_version}"
        notifier.notify_message(msg)
        return TaskResult(success=True, message=msg)

    # Make `StudyUpgraderTask` object is callable
    __call__ = run_task


class RawStudyInterface(StudyInterface):
    """
    Raw study business domain interface.

    Provides data from raw study service and applies commands instantly
    on underlying files.
    """

    def __init__(
        self,
        raw_service: RawStudyService,
        variant_service: VariantStudyService,
        user_service: LoginService,
        repository: StudyMetadataRepository,
        study: RawStudy,
    ):
        self._raw_study_service = raw_service
        self._variant_study_service = variant_service
        self._user_service = user_service
        self._repository = repository
        self._study = study
        self._cached_file_study: Optional[FileStudy] = None
        self._version = StudyVersion.parse(self._study.version)
        self._matrix_service = self._raw_study_service._matrix_service

    @override
    @property
    def id(self) -> str:
        return self._study.id

    @override
    @property
    def version(self) -> StudyVersion:
        return self._version

    @override
    def get_files(self) -> FileStudy:
        if not self._cached_file_study:
            self._cached_file_study = self._raw_study_service.get_raw(self._study)
        return self._cached_file_study

    @override
    def get_study_dao(self) -> ReadOnlyStudyDao:
        if self._study.storage_mode == StorageMode.DATABASE:
            return DatabaseStudyDao(self._study.id, db.session, self._matrix_service).read_only()
        command_context = self._variant_study_service.command_factory.command_context
        return FileStudyTreeDao(
            self.get_files(), command_context.generator_matrix_constants, command_context.blob_service
        ).read_only()

    @override
    def add_commands(self, commands: Sequence[ICommand], listener: Optional[ICommandListener] = None) -> None:
        study = self._study
        file_study: Optional[FileStudy] = None

        # Build DAO based on storage mode
        if study.storage_mode == StorageMode.DATABASE:
            dao: StudyDao = DatabaseStudyDao(study.id, db.session, self._matrix_service)
        else:
            file_study = self.get_files()
            command_context = self._variant_study_service.command_factory.command_context
            dao = FileStudyTreeDao(
                file_study,
                command_context.generator_matrix_constants,
                command_context.blob_service,
            )

        # Apply all commands
        should_invalidate_cache = False
        for command in commands:
            result = command.apply(dao, listener)
            if result.should_invalidate_cache:
                should_invalidate_cache = True
            if not result.status:
                raise CommandApplicationError(result.message)

        # Handle cache invalidation
        if should_invalidate_cache:
            remove_from_cache(self._raw_study_service.cache, study.id)
        elif study.storage_mode == StorageMode.FILESYSTEM:
            assert file_study is not None
            data = FileStudyTreeConfigDTO.from_build_config(file_study.config).model_dump()
            update_cache(self._raw_study_service.cache, study.id, data)

        # Update editor metadata
        self._update_editor_and_lastsave(dao)

        # Notify changes to child variants
        self._variant_study_service.on_parent_change(study.id)

    def _update_editor_and_lastsave(self, dao: StudyDao) -> None:
        user = self._user_service.get_identity(get_user_impersonator())
        if user:
            user_name = user.name or ""
            last_save = current_time().timestamp()
            # Update file (no-op for database storage mode)
            dao.update_antares_file(user_name, last_save)
            # Update DB metadata
            self._study.editor = user_name
            self._repository.save(self._study)


class VariantStudyInterface(StudyInterface):
    """
    Variant study business domain interface.

    Provides data from variant study service and simply append commands
    to the variant.
    """

    def __init__(self, variant_service: VariantStudyService, study: VariantStudy):
        self._variant_service = variant_service
        self._study = study
        self._version = StudyVersion.parse(self._study.version)

    @override
    @property
    def id(self) -> str:
        return self._study.id

    @override
    @property
    def version(self) -> StudyVersion:
        return self._version

    @override
    def get_files(self) -> FileStudy:
        return self._variant_service.get_raw(self._study)

    @override
    def get_study_dao(self) -> ReadOnlyStudyDao:
        command_context = self._variant_service.command_factory.command_context
        return FileStudyTreeDao(
            self.get_files(), command_context.generator_matrix_constants, command_context.blob_service
        ).read_only()

    @override
    def add_commands(self, commands: Sequence[ICommand], listener: Optional[ICommandListener] = None) -> None:
        # get current user if not in session, otherwise get session user
        self._variant_service.append_commands(self._study.id, transform_command_to_dto(commands, force_aggregate=True))


class StudyService:
    """
    Storage module facade service to handle studies management.
    """

    def __init__(
        self,
        raw_study_service: RawStudyService,
        variant_study_service: VariantStudyService,
        directory_service: DirectoryService,
        command_context: CommandContext,
        user_service: LoginService,
        repository: StudyMetadataRepository,
        job_result_repository: JobResultRepository,
        event_bus: IEventBus,
        file_transfer_manager: FileTransferManager,
        task_service: ITaskService,
        cache_service: ICache,
        config: Config,
    ):
        self.storage_service = StudyStorageService(raw_study_service, variant_study_service)
        self.user_service = user_service
        self.directory_service = directory_service
        self.repository = repository
        self.job_result_repository = job_result_repository
        self.event_bus = event_bus
        self.file_transfer_manager = file_transfer_manager
        self.task_service = task_service
        self.area_manager = AreaManager(command_context)
        self.layer_manager = LayerManager(command_context)
        self.district_manager = DistrictManager(command_context)
        self.links_manager = LinkManager(command_context)
        self.general_manager = GeneralManager(command_context)
        self.thematic_trimming_manager = ThematicTrimmingManager(command_context)
        self.optimization_manager = OptimizationManager(command_context)
        self.adequacy_patch_manager = AdequacyPatchManager(command_context)
        self.advanced_parameters_manager = AdvancedParamsManager(command_context)
        self.compatibility_parameters_manager = CompatibilityParamsManager(command_context)
        self.hydro_manager = HydroManager(command_context)
        self.allocation_manager = AllocationManager(command_context)
        self.renewable_manager = RenewableManager(command_context)
        self.thermal_manager = ThermalManager(command_context)
        self.st_storage_manager = STStorageManager(command_context)
        self.ts_config_manager = TimeSeriesConfigManager(command_context)
        self.playlist_manager = PlaylistManager(command_context)
        self.scenario_builder_manager = ScenarioBuilderManager(command_context)
        self.xpansion_manager = XpansionManager(command_context)
        self.matrix_manager = MatrixManager(command_context)
        self.binding_constraint_manager = BindingConstraintManager(command_context)
        self.correlation_manager = CorrelationManager(command_context)
        self.table_mode_manager = TableModeManager(
            self.area_manager,
            self.links_manager,
            self.thermal_manager,
            self.renewable_manager,
            self.st_storage_manager,
            self.binding_constraint_manager,
        )
        self.cache_service = cache_service
        self.config = config
        self.on_deletion_callbacks: List[Callable[[str], None]] = []
        matrix_service = command_context.matrix_service
        StudyDatabaseMatrixUsageProvider(matrix_service)
        self._study_dao_factories: dict[StorageMode, StudyFactoryDao] = {
            StorageMode.DATABASE: DatabaseStudyDaoFactory(matrix_service),
            StorageMode.FILESYSTEM: FileStudyDaoFactory(command_context, raw_study_service.study_factory),
        }

    def add_on_deletion_callback(self, callback: Callable[[str], None]) -> None:
        self.on_deletion_callbacks.append(callback)

    def _on_study_delete(self, uuid: str) -> None:
        """Run all callbacks"""
        for callback in self.on_deletion_callbacks:
            callback(uuid)

    def get(self, uuid: str, url: str, depth: int, formatted: bool) -> JSON:
        """
        Get study data inside filesystem
        Args:
            uuid: study uuid
            url: route to follow inside study structure
            depth: depth to expand tree when route matched
            formatted: indicate if raw files must be parsed and formatted

        Returns: data study formatted in json

        """
        study = self.get_study(uuid)
        assert_permission(study, StudyPermissionType.READ)

        return self.storage_service.get_storage(study).get(study, url, depth, formatted)

    def get_file(self, uuid: str, url: str) -> OriginalFile:
        """
        retrieve a file from a study folder

        Args:
            uuid: study uuid
            url: route to follow inside study structure

        Returns: data study formatted in json

        """
        study = self.get_study(uuid)
        assert_permission(study, StudyPermissionType.READ)

        output = self.storage_service.get_storage(study).get_file(study, url)

        return output

    def get_logs(self, study_id: str, output_id: str, job_id: str, err_log: bool) -> Optional[str]:
        study = self.get_study(study_id)
        assert_permission(study, StudyPermissionType.READ)
        file_study = self.get_file_study(study)
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
                # Assume UTF-8 but ignore errors, it's difficult to be sure of log encoding
                # especially because of windows error messages
                log = cast(
                    bytes,
                    file_study.tree.get(log_location, depth=1, formatted=True),
                ).decode(encoding="utf-8", errors="replace")
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
        file_study = self.get_file_study(study)
        file_study.tree.save(
            bytes(log_data, encoding="utf-8"),
            [
                "output",
                "logs",
                f"{job_id}-{log_suffix}",
            ],
        )
        stopwatch.log_elapsed(lambda d: logger.info(f"Saved logs for job {job_id} in {d}s"))

    def get_comments(self, study_id: str) -> str:
        """
        Get the comments of a study.

        Args:
            study_id: The ID of the study.

        Returns: textual comments of the study.
        """
        study = self.get_study(study_id)
        assert_permission(study, StudyPermissionType.READ)

        return self.get_study_interface(study).get_study_dao().get_comments()

    def set_comments(self, uuid: str, comments: str) -> None:
        """
        Replace data inside study.

        Args:
            uuid: study id
            comments: new comments to replace

        Returns: new data replaced

        """
        study = self.get_study(uuid)
        assert_permission(study, StudyPermissionType.WRITE)
        self.assert_study_unarchived(study)

        study_interface = self.get_study_interface(study)
        command_context = self.storage_service.variant_study_service.command_factory.command_context
        command = ReplaceComments(
            comments=comments,
            study_version=study_interface.version,
            command_context=command_context,
        )
        study_interface.add_commands([command])

    def get_studies_information(
        self,
        study_filter: StudyFilter,
        sort_by: Optional[StudySortBy] = None,
        pagination: StudyPagination = StudyPagination(),
    ) -> Dict[str, StudyMetadataDTO]:
        """
        Get information for matching studies of a search query.
        Args:
            study_filter: filtering parameters
            sort_by: how to sort the db query results
            pagination: set offset and limit for db query

        Returns: List of study information
        """
        logger.info("Retrieving matching studies")
        studies: Dict[str, StudyMetadataDTO] = {}
        matching_studies = self.repository.get_all(
            study_filter=study_filter,
            sort_by=sort_by,
            pagination=pagination,
        )
        logger.info("Studies retrieved")

        # Bulk optimization: pre-calculate all directory paths in one query
        directory_ids = [study.directory_id for study in matching_studies if study.directory_id is not None]
        directory_paths = self.directory_service.get_directory_paths_bulk(directory_ids)

        # Build study metadata with pre-calculated paths
        for study in matching_studies:
            folder_path = None
            if study.directory_id:
                dir_path = directory_paths.get(study.directory_id, "")
                folder_path = f"{dir_path}/{study.id}" if dir_path else study.id

            study_metadata = self._try_get_studies_information(study, folder_path)
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

    def _try_get_studies_information(
        self, study: Study, folder_path: Optional[str] = None
    ) -> Optional[StudyMetadataDTO]:
        try:
            return self.storage_service.get_storage(study).get_study_information(study, folder_path)
        except Exception as e:
            logger.warning(
                "Failed to build study %s (%s) metadata",
                study.id,
                study.path,
                exc_info=e,
            )
        return None

    def get_study_information(self, uuid: str) -> StudyMetadataDTO:
        """
        Retrieve study information.

        Args:
            uuid: The UUID of the study.

        Returns:
            Information about the study.
        """
        study = self.get_study(uuid)
        assert_permission(study, StudyPermissionType.READ)
        logger.info("Study metadata requested for study %s by user %s", uuid, get_user_id())
        # TODO: Debounce this with an "update_study_last_access" method updating only every few seconds.
        study.last_access = current_time()
        self.repository.save(study)
        return self.storage_service.get_storage(study).get_study_information(study)

    def update_study_information(self, uuid: str, metadata_patch: StudyMetadataPatchDTO) -> StudyMetadataDTO:
        """
        Update study metadata
        Args:
            uuid: study uuid
            metadata_patch: metadata patch
        """
        logger.info(
            "updating study %s metadata for user %s",
            uuid,
            get_user_id(),
        )
        study = self.get_study(uuid)
        assert_permission(study, StudyPermissionType.WRITE)

        if metadata_patch.author or metadata_patch.horizon:
            self.assert_study_unarchived(study)

        if metadata_patch.horizon:
            study_settings_url = "settings/generaldata/general"
            study_settings = self.storage_service.get_storage(study).get(study, study_settings_url)
            study_settings["horizon"] = metadata_patch.horizon
            self._edit_study_using_command(study=study, url=study_settings_url, data=study_settings)

        if metadata_patch.author or metadata_patch.name:
            study_antares_url = "study/antares"
            study_antares = self.storage_service.get_storage(study).get(study, study_antares_url)

            if metadata_patch.author:
                study_antares["author"] = metadata_patch.author

            if metadata_patch.name:
                study_antares["caption"] = metadata_patch.name

            self._edit_study_using_command(study=study, url=study_antares_url, data=study_antares)

        if metadata_patch.name:
            study.name = metadata_patch.name
        if metadata_patch.author:
            study.author = metadata_patch.author
        if metadata_patch.horizon:
            study.horizon = metadata_patch.horizon
        if metadata_patch.tags is not None:
            self.repository.update_tags(study, metadata_patch.tags)

        self.event_bus.push(
            Event(
                type=EventType.STUDY_DATA_EDITED,
                payload=study.to_json_summary(),
                permissions=PermissionInfo.from_study(study),
            )
        )

        remove_from_cache(cache=self.cache_service, root_id=study.id)
        return self.get_study_information(study.id)

    def check_study_access(self, uuid: str, permission: StudyPermissionType) -> Study:
        study = self.get_study(uuid)
        assert_permission(study, permission)
        self.assert_study_unarchived(study)
        return study

    def get_study_interface(self, study: Study) -> StudyInterface:
        """
        Creates the business interface to a particular study.
        """
        if isinstance(study, VariantStudy):
            return VariantStudyInterface(
                self.storage_service.variant_study_service,
                study,
            )
        elif isinstance(study, RawStudy):
            return RawStudyInterface(
                self.storage_service.raw_study_service,
                self.storage_service.variant_study_service,
                self.user_service,
                self.repository,
                study,
            )
        else:
            raise ValueError(f"Unsupported study type '{study.type}'")

    def get_file_study(self, study: Study) -> FileStudy:
        return self.storage_service.get_storage(study).get_raw(study)

    def get_study_path(self, uuid: str) -> Path:
        """
        Retrieve study path
        Args:
            uuid: study uuid

        Returns:

        """
        study = self.get_study(uuid)
        assert_permission(study, StudyPermissionType.RUN)

        logger.info("study %s path asked by user %s", uuid, get_user_id())
        return self.storage_service.get_storage(study).get_study_path(study)

    def create_study(
        self,
        study_name: str,
        version: Optional[StudyVersion],
        group_ids: List[str],
        storage_mode: StorageMode = StorageMode.FILESYSTEM,
        directory: str = "",
    ) -> str:
        """
        Creates a study with the specified study name, version, group IDs, and storage mode.

        Args:
            study_name: The name of the study to create.
            version: The version number of the study to choose the template for creation.
            group_ids: A possibly empty list of user group IDs to associate with the study.
            directory: Optional directory path where the study will be created (e.g., 'project/subfolder').
            storage_mode: The storage mode for the study (FILESYSTEM or DATABASE).

        Returns:
            str: The ID of the newly created study.

        Raises:
            UserHasNotPermissionError: If the user doesn't have permission for the specified groups.
        """
        owner, groups = self._validate_and_prepare_permissions(group_ids)

        sid = str(uuid4())
        study_path = self.config.get_workspace_path() / sid

        author = self.get_user_name()

        directory_id = self.directory_service.get_directory_by_path(directory)

        now_utc = current_time()
        raw = RawStudy(
            id=sid,
            name=study_name,
            workspace=DEFAULT_WORKSPACE_NAME,
            path=str(study_path),
            author=author,
            editor=author,
            created_at=now_utc,
            updated_at=now_utc,
            version=f"{version or NEW_DEFAULT_STUDY_VERSION:ddd}",
            storage_mode=storage_mode,
            directory_id=directory_id,
            owner=owner,
            groups=groups,
        )

        raw.content_status = StudyContentStatus.VALID
        self.repository.save(raw)
        self._study_dao_factories[raw.storage_mode].create_study_dao(raw)

        self.event_bus.push(
            Event(
                type=EventType.STUDY_CREATED,
                payload=raw.to_json_summary(),
                permissions=PermissionInfo.from_study(raw),
            )
        )

        logger.info("study %s created by user %s with storage_mode=%s", raw.id, get_user_id(), storage_mode)
        return str(raw.id)

    def get_user_name(self) -> str:
        """
        Returns the user's name
        If the logged user is a "bot" (i.e., an application's token), it returns the token's author name.
        """
        user = get_current_user()
        if user:
            user_id = user.impersonator if user.type == "bots" else user.id
            if curr_user := self.user_service.get_user(user_id):
                return curr_user.to_dto().name
        return "Unknown"

    def get_study_synthesis(self, study_id: str) -> FileStudyTreeConfigDTO:
        """
        Get the synthesis of a study.

        Args:
            study_id: The ID of the study.

        Returns: study synthesis
        """
        study = self.get_study(study_id)
        assert_permission(study, StudyPermissionType.READ)
        study.last_access = current_time()
        self.repository.save(study)
        study_storage_service = self.storage_service.get_storage(study)
        return study_storage_service.get_synthesis(study)

    def get_input_matrix_startdate(self, study_id: str, path: Optional[str]) -> MatrixIndex:
        study = self.get_study(study_id)
        assert_permission(study, StudyPermissionType.READ)
        file_study = self.get_file_study(study)
        output_id = None
        frequency = MatrixFrequency.HOURLY
        if path:
            path_components = path.strip().strip("/").split("/")
            if len(path_components) > 2 and path_components[0] == "output":
                output_id = path_components[1]
            data_node = file_study.tree.get_node(path_components)
            if isinstance(data_node, OutputSeriesMatrix) or isinstance(data_node, InputSeriesMatrix):
                frequency = data_node.freq
        return get_start_date(file_study, output_id, frequency)

    def remove_duplicates(self) -> None:
        duplicates = self.repository.list_duplicates()
        ids: List[str] = []
        # ids with same path
        duplicates_by_path = collections.defaultdict(list)
        for study_id, path in duplicates:
            duplicates_by_path[path].append(study_id)
        for path, study_ids in duplicates_by_path.items():
            ids.extend(study_ids[1:])
        if ids:  # Check if ids is not empty
            self.repository.delete(*ids)

    def sync_studies_on_disk(
        self, folders: List[StudyFolder], directory: Optional[Path] = None, recursive: bool = True
    ) -> None:
        """
        Used by watcher to send list of studies present on filesystem.

        Args:
            folders: list of studies currently present on folder
            directory: directory of studies that will be watched
            recursive: if False, the delta will apply only to the studies in "directory", otherwise
                it will apply to all studies having a path that descend from "directory".

        Returns:

        """
        now = current_time()
        clean_up_missing_studies_threshold = now - timedelta(days=MAX_MISSING_STUDY_TIMEOUT)
        all_studies = self.repository.get_all_raw()
        if directory:
            if recursive:
                all_studies = [raw_study for raw_study in all_studies if directory in Path(raw_study.path).parents]
            else:
                all_studies = [raw_study for raw_study in all_studies if directory == Path(raw_study.path).parent]
        all_studies = [study for study in all_studies if study.workspace != DEFAULT_WORKSPACE_NAME]
        folders = [folder for folder in folders if folder.workspace != DEFAULT_WORKSPACE_NAME]
        studies_by_path_workspace = {(study.workspace, study.path): study for study in all_studies}

        # delete orphan studies on database
        # key should be workspace, path to sync correctly studies with same path in different workspace
        workspace_paths = [(f.workspace, str(f.path)) for f in folders]

        for study in all_studies:
            if (
                isinstance(study, RawStudy)
                and not study.archived
                and (study.workspace, study.path) not in workspace_paths
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
                            payload=study.to_enhanced_json_summary(),
                            permissions=PermissionInfo.from_study(study),
                        )
                    )

                if study.missing and study.missing < clean_up_missing_studies_threshold:
                    logger.info(
                        "Study %s at %s is not present in disk and will be deleted",
                        study.id,
                        study.path,
                    )
                    self.repository.delete(study.id)

        # Add new studies
        study_paths = [(study.workspace, study.path) for study in all_studies if study.missing is None]
        missing_studies = {(study.workspace, study.path): study for study in all_studies if study.missing is not None}
        for folder in folders:
            study_path = str(folder.path)
            workspace = folder.workspace
            if (workspace, study_path) not in study_paths:
                try:
                    if (workspace, study_path) not in missing_studies.keys():
                        base_path = self.config.storage.workspaces[folder.workspace].path
                        dir_name = folder.path.relative_to(base_path)
                        study = RawStudy(
                            id=str(uuid4()),
                            name=folder.path.name,
                            path=study_path,
                            folder=str(dir_name),
                            workspace=workspace,
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
                        study = missing_studies[(workspace, study_path)]
                        study.missing = None
                        logger.info(
                            "Study at %s re appears on disk and will be added as %s",
                            study.path,
                            study.id,
                        )

                    self.storage_service.raw_study_service.update_from_raw_meta(study, fallback_on_default=True)
                    self.storage_service.raw_study_service.checks_antares_web_compatibility(study)

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
            elif directory and (workspace, study_path) in studies_by_path_workspace:
                existing_study = studies_by_path_workspace[(workspace, study_path)]
                if self.storage_service.raw_study_service.update_name_and_version_from_raw_meta(existing_study):
                    self.repository.save(existing_study)

    def delete_missing_studies(self) -> None:
        """
        Removes from the database any non-archived desktop studies whose folders
        no longer exist on disk. Used to clean up orphaned study entries.
        """
        all_studies = self.repository.get_all_raw()
        desktop_studies = [
            study
            for study in all_studies
            if study.workspace != DEFAULT_WORKSPACE_NAME and isinstance(study, RawStudy) and not study.archived
        ]

        def get_path(study: RawStudy) -> Path:
            wp = self.config.get_workspace_path(workspace=study.workspace)
            return wp / str(study.folder)

        missing_studies = [study for study in desktop_studies if not is_study_folder(get_path(study))]

        # delete orphan studies on database
        ids = [study.id for study in missing_studies]
        if ids:
            self.repository.delete(*ids)
            for study in missing_studies:
                self.event_bus.push(
                    Event(
                        type=EventType.STUDY_DELETED,
                        payload=study.to_enhanced_json_summary(),
                        permissions=PermissionInfo.from_study(study),
                    )
                )

    def copy_study(
        self,
        src_uuid: str,
        dest_study_name: str,
        group_ids: List[str],
        use_task: bool,
        destination_folder: PurePosixPath,
        output_ids: List[str],
        with_outputs: bool | None,
    ) -> str:
        """
        Create a new study by copying a reference study.

        This method is responsible for duplicating a study, optionally including its outputs.

        Output copy behavior:
            - If `with_outputs` is True and `output_ids` are specified: only the specified outputs are copied.
            - If `with_outputs` is True and `output_ids` is empty: all outputs are copied.
            - If `with_outputs` is False and `output_ids` are specified: an error is raised (incoherent configuration).
            - If `with_outputs` is False: no outputs are copied
            - If `with_outputs` is None and `output_ids` are specified: outputs will be copied; behaves like `with_outputs=True`.
            - If `with_outputs` is None and `output_ids` is empty: no outputs are copied.

        Args:
            src_uuid: The source study that you want to copy.
            dest_study_name: The name for the destination study.
            group_ids: A list of groups to assign to the destination study.
            use_task: indicate if the task job service should be used
            destination_folder: The path where the destination study should be created. If not provided, the default path will be used.
            output_ids: A list of output names that you want to include in the destination study.
            with_outputs: Indicates whether to copy the outputs as well.

        Returns:
            The newly created study.
        """
        if output_ids and with_outputs is False:
            raise IncorrectArgumentsForCopy("output_ids can only be used with with_outputs=True")

        src_study = self.get_study(src_uuid)
        assert_permission(src_study, StudyPermissionType.READ)
        self.assert_study_unarchived(src_study)

        owner, groups = self._validate_and_prepare_permissions(group_ids)

        def copy_task(notifier: ITaskNotifier) -> TaskResult:
            origin_study = self.get_study(src_uuid)
            study = self.storage_service.get_storage(origin_study).copy(
                origin_study,
                dest_study_name,
                group_ids,
                destination_folder,
                output_ids,
                with_outputs,
            )

            study.owner = owner
            study.groups = groups

            self._save_study(study)
            self.storage_service.raw_study_service.normalize_study(study)

            # Copying all jobs associated with the study
            jobs = self.job_result_repository.find_by_study_and_output_ids(origin_study.id, output_ids)

            new_jobs = [job.copy_jobs_for_study(study.id) for job in jobs]

            if new_jobs:
                self.job_result_repository.save_all(new_jobs)

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
                get_user_id(),
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
                progress=None,
                custom_event_messages=None,
            )
        else:
            res = copy_task(NoopNotifier())
            task_or_study_id = res.return_value or ""

        return task_or_study_id

    def move_study(self, study_id: str, folder_dest: str) -> None:
        study = self.get_study(study_id)
        assert_permission(study, StudyPermissionType.WRITE)
        if not is_managed(study):
            raise NotAManagedStudyException(study_id)

        if folder_dest:
            new_folder = folder_dest.rstrip("/") + f"/{study.id}"
            directory_id = self.directory_service.get_directory_by_path(folder_dest)
            study.directory_id = directory_id
        else:
            new_folder = None
            study.directory_id = None

        study.folder = new_folder
        self.repository.save(study)
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
        outputs: bool = True,
        archive_format: ArchiveFormat = ArchiveFormat.ZIP,
    ) -> FileDownloadTaskDTO:
        """
        Export study to a zip file.
        Args:
            uuid: study id
            outputs: integrate output folder in zip file
            archive_format: allow to choose between compression format

        """
        study = self.get_study(uuid)
        assert_permission(study, StudyPermissionType.READ)
        self.assert_study_unarchived(study)

        logger.info("Exporting study %s", uuid)
        export_name = f"Study {study.name} ({uuid}) export"

        export_file_download = self.file_transfer_manager.request_download(
            f"{study.name}-{uuid}{archive_format}", export_name
        )
        export_path = Path(export_file_download.path)
        export_id = export_file_download.id

        def export_task(notifier: ITaskNotifier) -> TaskResult:
            try:
                target_study = self.get_study(uuid)
                self.storage_service.get_storage(target_study).export_study(
                    target_study, export_path, outputs, archive_format
                )
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
            progress=None,
            custom_event_messages=None,
        )

        return FileDownloadTaskDTO(file=export_file_download.to_dto(), task=task_id)

    def export_study_flat(
        self,
        uuid: str,
        dest: Path,
        output_list: Optional[List[str]] = None,
    ) -> None:
        logger.info(f"Flat exporting study {uuid}")
        study = self.get_study(uuid)
        self.assert_study_unarchived(study)

        return self.storage_service.get_storage(study).export_study_flat(
            study, dest, len(output_list or []) > 0, output_list
        )

    def delete_study(self, uuid: str, children: bool) -> None:
        """
        Delete study and all its children

        Args:
            uuid: study uuid
            children: delete children or not
        """
        study = self.get_study(uuid)
        assert_permission(study, StudyPermissionType.WRITE)

        study_info = study.to_json_summary()

        # this prefetch the workspace because it is lazy loaded and the object is deleted
        # before using workspace attribute in raw study deletion
        # see https://github.com/AntaresSimulatorTeam/AntaREST/issues/606
        if isinstance(study, RawStudy):
            _ = study.workspace
            study_info = study.to_enhanced_json_summary()

        variant_service = self.storage_service.variant_study_service

        if variant_service.has_children(study):
            if not children:
                raise StudyDeletionNotAllowed(study.id, "Study has variant children")

            variant_service.walk_children(
                study.id,
                lambda s: self.delete_study(s.id, True),
                bottom_first=True,
                include_parent=False,
            )

        # If the study is a variant, and its snapshot is generating,
        # we need to wait until it's done to delete it to avoid any fs issues
        if isinstance(study, VariantStudy) and study.generation_task:
            self.task_service.await_task(study.generation_task, 600)

        self.repository.delete(study.id)

        # delete the files afterward for
        # if the study cannot be deleted from database for foreign key reason
        if self.assert_study_unarchived(study=study, raise_exception=False):
            self.storage_service.get_storage(study).delete(study)
        else:
            if isinstance(study, RawStudy):
                os.unlink(self.storage_service.raw_study_service.find_archive_path(study))

        self.event_bus.push(
            Event(
                type=EventType.STUDY_DELETED,
                payload=study_info,
                permissions=PermissionInfo.from_study(study),
            )
        )
        logger.info("study %s deleted by user %s", uuid, get_user_id())

        self._on_study_delete(uuid=uuid)

    def import_study(
        self,
        stream: BinaryIO,
        group_ids: List[str],
    ) -> str:
        """
        Import a compressed study.

        Args:
            stream: binary content of the study compressed in ZIP or 7z format.
            group_ids: group to attach to study

        Returns:
            New study UUID.

        Raises:
            BadArchiveContent: If the archive is corrupted or in an unknown format.
            UserHasNotPermissionError: If the user doesn't have permission for the specified groups.
        """
        owner, groups = self._validate_and_prepare_permissions(group_ids)

        sid = str(uuid4())
        path = str(self.config.get_workspace_path() / sid)
        study = RawStudy(
            id=sid,
            workspace=DEFAULT_WORKSPACE_NAME,
            path=path,
            editor=self.get_user_name(),
            public_mode=PublicMode.NONE if group_ids else PublicMode.READ,
            owner=owner,
            groups=groups,
        )
        study = self.storage_service.raw_study_service.import_study(study, stream)
        study.updated_at = current_time()

        self._save_study(study)
        self.storage_service.raw_study_service.normalize_study(study)
        self.event_bus.push(
            Event(
                type=EventType.STUDY_CREATED,
                payload=study.to_json_summary(),
                permissions=PermissionInfo.from_study(study),
            )
        )

        logger.info("study %s imported by user %s", study.id, get_user_id())
        return study.id

    def _create_edit_study_command(
        self, tree_node: INode[JSON, SUB_JSON, JSON], url: str, data: SUB_JSON, study_version: StudyVersion
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
            assert not isinstance(data, (bytes, list))
            return UpdateConfig(target=url, data=data, command_context=context, study_version=study_version)
        elif isinstance(tree_node, InputSeriesMatrix):
            if isinstance(data, bytes):
                # noinspection PyTypeChecker
                matrix = imports_matrix_from_bytes(data)
                if matrix is None:
                    raise MatrixImportFailed("Could not parse the given matrix")
                matrix = matrix.reshape((1, 0)) if matrix.size == 0 else matrix
                return ReplaceMatrix(
                    target=url, matrix=matrix.tolist(), command_context=context, study_version=study_version
                )
            assert isinstance(data, (list, str))
            return ReplaceMatrix(target=url, matrix=data, command_context=context, study_version=study_version)
        elif isinstance(tree_node, RawFileNode):
            if url.split("/")[-1] == "comments":
                if isinstance(data, bytes):
                    data = data.decode("utf-8")
                assert isinstance(data, str)
                return ReplaceComments(comments=data, command_context=context, study_version=study_version)
            elif isinstance(data, bytes):
                return UpdateRawFile(
                    target=url,
                    b64Data=base64.b64encode(data).decode("utf-8"),
                    command_context=context,
                    study_version=study_version,
                )
        raise NotImplementedError()

    def _create_replace_user_resource_command(
        self, version: StudyVersion, data: SUB_JSON, file_relpath: PurePosixPath
    ) -> ICommand:
        # We should make sure the path is located inside the user folder. Otherwise, we raise an Exception
        user_path = _get_path_inside_user_folder(str(file_relpath), ResourceCreationNotAllowed)
        # Save the content inside the blob service and create the command.
        content = data or b""
        assert isinstance(content, bytes)
        context = self.storage_service.variant_study_service.command_factory.command_context
        blob_id = context.blob_service.save(content)
        args = {"path": user_path, "resource_type": ResourceType.FILE, "blob_id": blob_id}
        command_data = UserResourceDataCreation.model_validate(args)
        return ReplaceUserResource(data=command_data, command_context=context, study_version=version)

    def _edit_study_using_command(self, study: Study, url: str, data: SUB_JSON) -> List[ICommand]:
        """
        Replace data on disk with new, using variant commands.

        In addition to regular configuration changes, this function also allows the end user
        to store files on disk, in the "user" directory of the study (without using variant commands).

        Args:
            study: study
            url: data path to reach
            data: new data to replace
        """
        study_service = self.storage_service.get_storage(study)
        file_study = study_service.get_raw(metadata=study)
        version = file_study.config.version

        command: ICommand
        file_relpath = PurePosixPath(url.strip().strip("/"))

        try:
            # A ChildNotFoundError is raised if the file does not exist.
            tree_node = file_study.tree.get_node(list(file_relpath.parts))
            # A ResourceCreationNotAllowed is raised if the path isn't located inside the user folder
            _get_path_inside_user_folder(str(file_relpath), ResourceCreationNotAllowed)
            # We're modifying an existing resource inside the user folder.
            command = self._create_replace_user_resource_command(version, data, file_relpath)

        except ChildNotFoundError:
            # We're creating a resource
            command = self._create_replace_user_resource_command(version, data, file_relpath)

        except ResourceCreationNotAllowed:
            # We're modifying an existing resource outside the user folder
            command = self._create_edit_study_command(tree_node, url, data, version)

        commands = [command]
        self.get_study_interface(study).add_commands(commands)
        return commands  # for testing purpose

    def apply_commands(self, uuid: str, commands: List[CommandDTO]) -> Optional[List[str]]:
        study = self.get_study(uuid)
        if isinstance(study, VariantStudy):
            return self.storage_service.variant_study_service.append_commands(uuid, commands)
        else:
            assert_permission(study, StudyPermissionType.WRITE)
            self.assert_study_unarchived(study)
            parsed_commands: List[ICommand] = []
            for command in commands:
                parsed_commands.extend(self.storage_service.variant_study_service.command_factory.to_command(command))
            self.get_study_interface(study).add_commands(parsed_commands)

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
            get_user_id(),
        )
        return None

    def edit_study(self, uuid: str, url: str, new: SUB_JSON) -> JSON:
        """
        Replace data inside study.

        Args:
            uuid: study id
            url: path data target in study
            new: new data to replace

        Returns: new data replaced
        """
        study = self.get_study(uuid)
        assert_permission(study, StudyPermissionType.WRITE)
        self.assert_study_unarchived(study)

        self._edit_study_using_command(study=study, url=url.strip().strip("/"), data=new)

        self.event_bus.push(
            Event(
                type=EventType.STUDY_DATA_EDITED,
                payload=study.to_json_summary(),
                permissions=PermissionInfo.from_study(study),
            )
        )
        logger.info("data %s on study %s updated by user %s", url, uuid, get_user_id())
        return cast(JSON, new)

    def change_owner(self, study_id: str, owner_id: int) -> None:
        """
        Change study owner
        Args:
            study_id: study uuid
            owner_id: new owner id

        Returns:

        """
        study = self.get_study(study_id)
        assert_permission(study, StudyPermissionType.MANAGE_PERMISSIONS)
        self.assert_study_unarchived(study)
        new_owner = self.user_service.get_user(owner_id)
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
            get_user_id(),
            study_id,
            owner_id,
        )

    def add_group(self, study_id: str, group_id: str) -> None:
        """
        Attach new group on study.

        Args:
            study_id: study uuid
            group_id: group id to attach

        Returns:

        """
        study = self.get_study(study_id)
        assert_permission(study, StudyPermissionType.MANAGE_PERMISSIONS)
        group = self.user_service.get_group(group_id)
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
            get_user_id(),
        )

    def remove_group(self, study_id: str, group_id: str) -> None:
        """
        Detach group on study
        Args:
            study_id: study uuid
            group_id: group to detach

        Returns:

        """
        study = self.get_study(study_id)
        assert_permission(study, StudyPermissionType.MANAGE_PERMISSIONS)
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
            get_user_id(),
        )

    def set_public_mode(self, study_id: str, mode: PublicMode) -> None:
        """
        Update public mode permission on study
        Args:
            study_id: study uuid
            mode: new public permission

        Returns:

        """
        study = self.get_study(study_id)
        assert_permission(study, StudyPermissionType.MANAGE_PERMISSIONS)
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
            get_user_id(),
        )

    def get_all_areas_info(
        self,
        uuid: str,
    ) -> List[AreaInfo]:
        study = self.get_study(uuid)
        assert_permission(study, StudyPermissionType.READ)
        study_interface = self.get_study_interface(study)
        return self.area_manager.get_all_areas_info(study_interface)

    def get_all_areas_ui_info(
        self,
        uuid: str,
    ) -> Dict[str, AreaUIData]:
        study = self.get_study(uuid)
        assert_permission(study, StudyPermissionType.READ)
        study_interface = self.get_study_interface(study)
        return self.area_manager.get_all_areas_ui_info(study_interface)

    def get_all_links(
        self,
        uuid: str,
    ) -> List[Link]:
        study = self.get_study(uuid)
        assert_permission(study, StudyPermissionType.READ)
        return self.links_manager.get_all_links(self.get_study_interface(study))

    def create_area(
        self,
        uuid: str,
        area_creation_dto: AreaCreation,
    ) -> AreaInfo:
        study = self.get_study(uuid)
        assert_permission(study, StudyPermissionType.WRITE)
        self.assert_study_unarchived(study)
        new_area = self.area_manager.create_area(self.get_study_interface(study), area_creation_dto)
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
        link_creation_dto: Link,
    ) -> Link:
        study = self.get_study(uuid)
        assert_permission(study, StudyPermissionType.WRITE)
        self.assert_study_unarchived(study)
        new_link = self.links_manager.create_link(self.get_study_interface(study), link_creation_dto)
        self.event_bus.push(
            Event(
                type=EventType.STUDY_DATA_EDITED,
                payload=study.to_json_summary(),
                permissions=PermissionInfo.from_study(study),
            )
        )
        return new_link

    def update_link(
        self,
        uuid: str,
        area_from: str,
        area_to: str,
        link_update_dto: LinkUpdate,
    ) -> Link:
        study = self.get_study(uuid)
        assert_permission(study, StudyPermissionType.WRITE)
        self.assert_study_unarchived(study)
        updated_link = self.links_manager.update_link(
            self.get_study_interface(study), area_from, area_to, link_update_dto
        )
        self.event_bus.push(
            Event(
                type=EventType.STUDY_DATA_EDITED,
                payload=study.to_json_summary(),
                permissions=PermissionInfo.from_study(study),
            )
        )
        return updated_link

    def update_area_ui(
        self,
        uuid: str,
        area_id: str,
        area_ui: AreaUIUpdate,
        layer: str,
    ) -> None:
        study = self.get_study(uuid)
        assert_permission(study, StudyPermissionType.WRITE)
        self.assert_study_unarchived(study)
        return self.area_manager.update_area_ui(self.get_study_interface(study), area_id, area_ui, layer)

    def delete_area(self, uuid: str, area_id: str) -> None:
        """
        Delete area from study if it is not referenced by a binding constraint,
        otherwise raise an HTTP 403 Forbidden error.

        Args:
            uuid: The study ID.
            area_id: The area ID to delete.

        Raises:
            ReferencedObjectDeletionNotAllowed: If the area is referenced by a binding constraint.
        """
        study = self.get_study(uuid)
        assert_permission(study, StudyPermissionType.WRITE)
        study_interface = self.get_study_interface(study)
        self.assert_study_unarchived(study)
        # Checks the area is not referenced in any constraint
        referencing_binding_constraints = self.binding_constraint_manager.get_binding_constraints(
            study_interface, ConstraintFilters(area_name=area_id)
        )
        if referencing_binding_constraints:
            binding_ids = [bc.id for bc in referencing_binding_constraints]
            raise ReferencedObjectDeletionNotAllowed(area_id, binding_ids, object_type="Area")

        # Delete the area
        self.area_manager.delete_area(study_interface, area_id)
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
    ) -> None:
        """
        Delete link from study if it is not referenced by a binding constraint,
        otherwise raise an HTTP 403 Forbidden error.

        Args:
            uuid: The study ID.
            area_from: The area from which the link starts.
            area_to: The area to which the link ends.

        Raises:
            ReferencedObjectDeletionNotAllowed: If the link is referenced by a binding constraint.
        """
        study = self.get_study(uuid)
        assert_permission(study, StudyPermissionType.WRITE)
        self.assert_study_unarchived(study)
        study_interface = self.get_study_interface(study)
        link_id = LinkTerm(area1=area_from, area2=area_to).generate_id()
        referencing_binding_constraints = self.binding_constraint_manager.get_binding_constraints(
            study_interface, ConstraintFilters(link_id=link_id)
        )
        if referencing_binding_constraints:
            binding_ids = [bc.id for bc in referencing_binding_constraints]
            raise ReferencedObjectDeletionNotAllowed(link_id, binding_ids, object_type="Link")
        self.links_manager.delete_link(study_interface, area_from, area_to)
        self.event_bus.push(
            Event(
                type=EventType.STUDY_DATA_EDITED,
                payload=study.to_json_summary(),
                permissions=PermissionInfo.from_study(study),
            )
        )

    def archive(self, uuid: str) -> str:
        logger.info(f"Archiving study {uuid}")
        study = self.get_study(uuid)
        assert_permission(study, StudyPermissionType.WRITE)

        self.assert_study_unarchived(study)

        if not isinstance(study, RawStudy):
            raise UnsupportedOperationOnThisStudyType(study.id, "archive", "raw")

        if not is_managed(study):
            raise NotAManagedStudyException(study.id)

        if self.task_service.list_tasks(
            TaskListFilter(
                ref_id=uuid,
                type=[TaskType.ARCHIVE, TaskType.UNARCHIVE],
                status=[TaskStatus.RUNNING, TaskStatus.PENDING],
            )
        ):
            raise TaskAlreadyRunning()

        def archive_task(notifier: ITaskNotifier) -> TaskResult:
            study_to_archive = self.get_study(uuid)
            study_to_archive = assert_raw(study_to_archive)
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
            progress=None,
            custom_event_messages=None,
        )

    def unarchive(self, uuid: str) -> str:
        study = self.get_study(uuid)
        if not study.archived:
            raise HTTPException(http.HTTPStatus.BAD_REQUEST, "Study is not archived")

        if self.task_service.list_tasks(
            TaskListFilter(
                ref_id=uuid,
                type=[TaskType.UNARCHIVE, TaskType.ARCHIVE],
                status=[TaskStatus.RUNNING, TaskStatus.PENDING],
            )
        ):
            raise TaskAlreadyRunning()

        assert_permission(study, StudyPermissionType.WRITE)

        if not isinstance(study, RawStudy):
            raise UnsupportedOperationOnThisStudyType(study.id, "unarchive", "raw")

        def unarchive_task(notifier: ITaskNotifier) -> TaskResult:
            study_to_archive = self.get_study(uuid)
            study_to_archive = assert_raw(study_to_archive)
            self.storage_service.raw_study_service.unarchive(study_to_archive)
            study_to_archive.archived = False

            os.unlink(self.storage_service.raw_study_service.find_archive_path(study_to_archive))
            self.repository.save(study_to_archive)
            self.event_bus.push(
                Event(
                    type=EventType.STUDY_EDITED,
                    payload=study_to_archive.to_json_summary(),
                    permissions=PermissionInfo.from_study(study_to_archive),
                )
            )
            remove_from_cache(cache=self.cache_service, root_id=uuid)
            return TaskResult(success=True, message="ok")

        return self.task_service.add_task(
            unarchive_task,
            f"Study {study.name} unarchiving",
            task_type=TaskType.UNARCHIVE,
            ref_id=study.id,
            progress=None,
            custom_event_messages=None,
        )

    def _validate_and_prepare_permissions(self, group_ids: Sequence[str]) -> tuple[Any, List[Group]]:
        """
        Validate that the current user has permissions for the specified groups.

        Args:
            group_ids: The list of group IDs to validate.

        Returns:
            A tuple containing:
            - The owner (User) from the database
            - The list of validated Group objects

        Raises:
            UserHasNotPermissionError:
                If the owner is not specified, has invalid authentication,
                or does not have permission for any of the specified group IDs.
        """
        current_user = get_current_user()
        if not current_user:
            raise UserHasNotPermissionError("owner is not specified or has invalid authentication")

        owner = self.user_service.get_user(current_user.impersonator)

        groups: List[Group] = []
        for gid in group_ids:
            owned_groups = (g for g in current_user.groups if g.id == gid)
            jwt_group: Optional[JWTGroup] = next(owned_groups, None)
            if jwt_group is None or jwt_group.role is None:
                raise UserHasNotPermissionError(f"Permission denied for group ID: {gid}")
            groups.append(Group(id=jwt_group.id, name=jwt_group.name))

        return owner, groups

    def _save_study(
        self,
        study: Study,
    ) -> None:
        """
        Save a study to the database.

        This function is responsible for saving a study to the repository.
        The study's owner and groups should already be set before calling this method.

        Args:
            study: The study to be saved.
        """
        if isinstance(study, RawStudy):
            study.content_status = StudyContentStatus.VALID

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

    def assert_study_unarchived(self, study: Study, raise_exception: bool = True) -> bool:
        if study.archived and raise_exception:
            raise UnsupportedOperationOnArchivedStudy(study.id)
        return not study.archived

    # noinspection PyUnusedLocal
    @staticmethod
    def get_studies_versions() -> List[str]:
        return sorted([str(v) for v in STUDY_REFERENCE_TEMPLATES])

    def create_xpansion_configuration(
        self,
        uuid: str,
    ) -> None:
        study = self.get_study(uuid)
        assert_permission(study, StudyPermissionType.WRITE)
        self.assert_study_unarchived(study)
        study_interface = self.get_study_interface(study)
        self.xpansion_manager.create_xpansion_configuration(study_interface)

    def delete_xpansion_configuration(self, uuid: str) -> None:
        study = self.get_study(uuid)
        assert_permission(study, StudyPermissionType.WRITE)
        self.assert_study_unarchived(study)
        study_interface = self.get_study_interface(study)
        self.xpansion_manager.delete_xpansion_configuration(study_interface)

    def get_xpansion_settings(self, uuid: str) -> XpansionSettings:
        study = self.get_study(uuid)
        assert_permission(study, StudyPermissionType.READ)
        study_interface = self.get_study_interface(study)
        return self.xpansion_manager.get_xpansion_settings(study_interface)

    def update_xpansion_settings(self, uuid: str, xpansion_settings_dto: XpansionSettingsUpdate) -> XpansionSettings:
        study = self.get_study(uuid)
        assert_permission(study, StudyPermissionType.READ)
        self.assert_study_unarchived(study)
        study_interface = self.get_study_interface(study)
        return self.xpansion_manager.update_xpansion_settings(study_interface, xpansion_settings_dto)

    def add_candidate(
        self,
        uuid: str,
        xpansion_candidate: XpansionCandidateCreation,
    ) -> XpansionCandidate:
        study = self.get_study(uuid)
        assert_permission(study, StudyPermissionType.WRITE)
        self.assert_study_unarchived(study)
        study_interface = self.get_study_interface(study)
        return self.xpansion_manager.add_candidate(study_interface, xpansion_candidate)

    def get_candidate(self, uuid: str, candidate_name: str) -> XpansionCandidate:
        study = self.get_study(uuid)
        assert_permission(study, StudyPermissionType.READ)
        study_interface = self.get_study_interface(study)
        return self.xpansion_manager.get_candidate(study_interface, candidate_name)

    def get_candidates(self, uuid: str) -> List[XpansionCandidate]:
        study = self.get_study(uuid)
        assert_permission(study, StudyPermissionType.READ)
        study_interface = self.get_study_interface(study)
        return self.xpansion_manager.get_candidates(study_interface)

    def replace_xpansion_candidate(
        self,
        uuid: str,
        candidate_name: str,
        xpansion_candidate: XpansionCandidateCreation,
    ) -> XpansionCandidate:
        study = self.get_study(uuid)
        assert_permission(study, StudyPermissionType.READ)
        self.assert_study_unarchived(study)
        study_interface = self.get_study_interface(study)
        return self.xpansion_manager.replace_candidate(study_interface, candidate_name, xpansion_candidate)

    def delete_xpansion_candidate(self, uuid: str, candidate_name: str) -> None:
        study = self.get_study(uuid)
        assert_permission(study, StudyPermissionType.READ)
        self.assert_study_unarchived(study)
        study_interface = self.get_study_interface(study)
        self.xpansion_manager.delete_candidate(study_interface, candidate_name)

    def update_xpansion_constraints_settings(self, uuid: str, constraints_file_name: str) -> XpansionSettings:
        study = self.get_study(uuid)
        assert_permission(study, StudyPermissionType.WRITE)
        self.assert_study_unarchived(study)
        study_interface = self.get_study_interface(study)
        return self.xpansion_manager.update_xpansion_constraints_settings(study_interface, constraints_file_name)

    def update_matrix(self, uuid: str, path: str, matrix_edit_instruction: List[MatrixEditInstruction]) -> None:
        """
        Updates a matrix in a study based on the provided edit instructions.

        Args:
            uuid: The UUID of the study.
            path: The path of the matrix to update.
            matrix_edit_instruction: A list of edit instructions to be applied to the matrix.

        Raises:
            BadEditInstructionException: If an error occurs while updating the matrix.

        Permissions:
            - User must have WRITE permission on the study.
        """
        study = self.get_study(uuid)
        assert_permission(study, StudyPermissionType.WRITE)
        self.assert_study_unarchived(study)
        study_interface = self.get_study_interface(study)
        try:
            self.matrix_manager.update_matrix(study_interface, path, matrix_edit_instruction)
        except MatrixManagerError as exc:
            raise BadEditInstructionException(str(exc)) from exc

    def generate_timeseries(self, study: Study, outage_details: bool) -> str:
        task_name = f"Generating thermal timeseries for study {study.name} ({study.id})"
        study_tasks = self.task_service.list_tasks(
            TaskListFilter(
                ref_id=study.id,
                type=[TaskType.THERMAL_CLUSTER_SERIES_GENERATION],
                status=[TaskStatus.RUNNING, TaskStatus.PENDING],
            )
        )
        if len(study_tasks) > 0:
            raise TaskAlreadyRunning()

        thermal_cluster_timeseries_generation_task = ThermalClusterTimeSeriesGeneratorTask(
            study.id,
            repository=self.repository,
            storage_service=self.storage_service,
            event_bus=self.event_bus,
            study_interface_supplier=self.get_study_interface,
            thermal_outage_details=outage_details,
        )

        return self.task_service.add_task(
            thermal_cluster_timeseries_generation_task,
            task_name,
            task_type=TaskType.THERMAL_CLUSTER_SERIES_GENERATION,
            ref_id=study.id,
            progress=0,
            custom_event_messages=None,
        )

    def upgrade_study(self, study_id: str, target_version: str) -> str:
        study = self.get_study(study_id)
        assert_permission(study, StudyPermissionType.WRITE)
        self.assert_study_unarchived(study)

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
        study_version = StudyVersion.parse(study.version)
        if target_version:
            parsed_target_version = StudyVersion.parse(target_version)
            check_versions_coherence(study_version, parsed_target_version)
        else:
            parsed_target_version = find_next_version(study_version)

        task_name = f"Upgrade study {study.name} ({study.id}) to version {parsed_target_version}"
        study_tasks = self.task_service.list_tasks(
            TaskListFilter(
                ref_id=study_id,
                type=[TaskType.UPGRADE_STUDY],
                status=[TaskStatus.RUNNING, TaskStatus.PENDING],
            )
        )
        if len(study_tasks) > 0:
            raise TaskAlreadyRunning()

        study_upgrader_task = StudyUpgraderTask(
            study_id,
            parsed_target_version,
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
            progress=None,
            custom_event_messages=None,
        )

    def get_disk_usage(self, uuid: str) -> int:
        """
        Calculates the size of the disk used to store the study if the user has permissions.

        The calculation of disk space concerns the entire study directory.
        In the case of a variant, the snapshot folder must be taken into account, as well as the outputs.

        Args:
            uuid: the study ID.

        Returns:
            Disk usage of the study in bytes.

        Raises:
            UserHasNotPermissionError: If the user does not have the READ permissions (HTTP status 403).
        """
        study = self.get_study(uuid=uuid)
        assert_permission(study, StudyPermissionType.READ)
        study_path = self.storage_service.raw_study_service.get_study_path(study)
        # If the study is a variant, it's possible that it only exists in DB and not on disk. If so, we return 0.
        return get_disk_usage(study_path) if study_path.exists() else 0

    def get_matrix_with_index_and_header(
        self, *, study_id: str, path: str, with_index: bool, with_header: bool
    ) -> pd.DataFrame:
        """
        Retrieves a matrix from a study with the option to include the index and header.

        Args:
            study_id: The UUID of the study from which to retrieve the matrix.
            path: The relative path to the matrix within the study.
            with_index: A boolean indicating whether to include the index in the retrieved matrix.
            with_header: A boolean indicating whether to include the header in the retrieved matrix.

        Returns:
            A DataFrame representing the matrix.

        Raises:
            HTTPException: If the matrix does not exist or the user does not have the necessary permissions.
        """

        matrix_path = Path(path)
        study = self.get_study(study_id)
        study_interface = self.get_study_interface(study)

        url = matrix_path.parts
        if url in [("input", "hydro", "allocation"), ("input", "hydro", "correlation")]:
            if url[-1] == "allocation":
                hydro_matrix: HydroCorrelationMatrix | HydroAllocationMatrix = (
                    self.allocation_manager.get_allocation_matrix(study_interface)
                )
            else:
                hydro_matrix = self.correlation_manager.get_correlation_matrix(study_interface)
            return pd.DataFrame(data=hydro_matrix.data, columns=hydro_matrix.columns, index=hydro_matrix.index)

        # Checks that the provided path refers to a matrix
        node = self.get_file_study(study).tree.get_node(list(url))
        if isinstance(node, MatrixNode):
            pandas_df = node.parse_as_dataframe().to_pandas()
        elif isinstance(node, OutputSeriesMatrix):
            pandas_df = node.parse_dataframe()
            pandas_df.columns = pd.Index(pandas_df.columns)
        elif isinstance(node, OutputSynthesis):
            pandas_df = pd.DataFrame(**node.load())
        else:
            raise IncorrectPathError(f"The provided path does not point to a valid matrix: '{path}'")

        if with_index:
            matrix_index = self.get_input_matrix_startdate(study_id, path)
            time_column = pd.date_range(
                start=matrix_index.start_date, periods=len(pandas_df), freq=matrix_index.level.value[0]
            )
            pandas_df.index = time_column

        adjust_matrix_columns_index(
            pandas_df,
            path,
            with_index=with_index,
            with_header=with_header,
            study_version=study_interface.version,
        )

        return pandas_df

    def asserts_no_thermal_in_binding_constraints(self, study: Study, area_id: str, cluster_ids: Sequence[str]) -> None:
        """
        Check that no cluster is referenced in a binding constraint, otherwise raise an HTTP 403 Forbidden error.

        Args:
            study: input study for which an update is to be committed
            area_id: area ID to be checked
            cluster_ids: IDs of the thermal clusters to be checked

        Raises:
            ReferencedObjectDeletionNotAllowed: if a cluster is referenced in a binding constraint
        """

        study_interface = self.get_study_interface(study)
        for cluster_id in cluster_ids:
            ref_bcs = self.binding_constraint_manager.get_binding_constraints(
                study_interface, ConstraintFilters(cluster_id=f"{area_id}.{cluster_id}")
            )
            if ref_bcs:
                binding_ids = [bc.id for bc in ref_bcs]
                raise ReferencedObjectDeletionNotAllowed(cluster_id, binding_ids, object_type="Cluster")

    def delete_user_file_or_folder(self, study_id: str, path: str) -> None:
        """
        Deletes a file or a folder of the study.
        The data must be located inside the 'User' folder.
        Also, it can not be inside the 'expansion' folder.

        Args:
            study_id: UUID of the concerned study
            path: Path corresponding to the resource to be deleted

        Raises:
            ResourceDeletionNotAllowed: if the path does not comply with the above rules
        """
        args = {"path": _get_path_inside_user_folder(path, ResourceDeletionNotAllowed)}
        cmd_data = UserResourceDataRemoval(**args)
        self._alter_user_folder(study_id, cmd_data, RemoveUserResource, ResourceDeletionNotAllowed)

    def create_user_folder(self, study_id: str, path: str) -> None:
        """
        Creates a folder inside the study.
        The data must be located inside the 'User' folder.
        Also, it can not be inside the 'expansion' folder.

        Args:
            study_id: UUID of the concerned study
            path: Path corresponding to the resource to be deleted

        Raises:
            ResourceCreationNotAllowed: if the path does not comply with the above rules
        """
        args = {
            "path": _get_path_inside_user_folder(path, ResourceCreationNotAllowed),
            "resource_type": ResourceType.FOLDER,
        }
        command_data = UserResourceDataCreation.model_validate(args)
        self._alter_user_folder(study_id, command_data, ReplaceUserResource, ResourceCreationNotAllowed)

    def _alter_user_folder(
        self,
        study_id: str,
        command_data: UserResourceDataCreation | UserResourceDataRemoval,
        command_class: Type[ReplaceUserResource | RemoveUserResource],
        exception_class: Type[ResourceCreationNotAllowed | ResourceDeletionNotAllowed],
    ) -> None:
        study = self.get_study(study_id)
        assert_permission(study, StudyPermissionType.WRITE)

        args = {
            "data": command_data,
            "study_version": study.version,
            "command_context": self.storage_service.variant_study_service.command_factory.command_context,
        }
        command = command_class.model_validate(args)
        file_study = self.get_file_study(study)
        try:
            self.get_study_interface(study).add_commands([command])
        except CommandApplicationError as e:
            raise exception_class(e.detail) from e

        # update cache
        cache_id = study_raw_cache_key(study.id)
        updated_tree = file_study.tree.get()
        self.storage_service.get_storage(study).cache.put(cache_id, updated_tree)  # type: ignore

    def normalize_study_by_id(self, study_id: str) -> None:
        """
        Performs several verifications before normalizing a study.
        """
        study = self.get_study(study_id)
        assert_permission(study, StudyPermissionType.READ)  # We're not really modifying the study

        if not is_managed(study):
            raise NotAManagedStudyException(study_id)
        if isinstance(study, VariantStudy):
            raise UnsupportedOperationOnThisStudyType(study_id, "normalize", "raw")
        self.assert_study_unarchived(study)

        self.storage_service.raw_study_service.normalize_study(study)

    def get_raw_content(self, uuid: str, path: str, depth: int, formatted: bool) -> Any:
        """
        Returns the content of a node based on the provided arguments.

        Depending on the type of node, it may return the following types of data:
          - an arbitrary dictionary (ini files ...)
          - a dataframe (input matrices ...)
          - raw file content (arbitrary user files ...)

        This allows callers to handle the result as most appropriate.
        """
        study = self.get_study(uuid)
        assert_permission(study, StudyPermissionType.READ)
        self.assert_study_unarchived(study)
        file_study = self.get_file_study(study)
        url = [item for item in path.split("/") if item]
        node, relative_url = file_study.tree.get_node_and_remainder(url)

        # Return a dataframe when possible instead of less memory & computation - efficient python objects
        if isinstance(node, MatrixNode):
            return node.parse_as_dataframe()

        return node.get(url=relative_url, depth=depth, formatted=formatted)

    def get_study_data(self, uuid: str) -> StudyDataDTO:
        study = self.get_study(uuid)
        assert_permission(study, StudyPermissionType.READ)
        study_interface = self.get_study_interface(study)

        ##########################
        # Study metadata
        ##########################

        obj: dict[str, Any] = {
            "metadata": {"version": study_interface.version, "name": study.name, "folder": study.folder}
        }

        ##########################
        # Areas
        ##########################

        area_properties = self.area_manager.get_all_area_properties(study_interface)
        area_names = {a.id: a.name for a in self.area_manager.get_all_areas_info(study_interface)}
        thermal_clusters = self.thermal_manager.get_all_thermals_props(study_interface)
        st_storages = self.st_storage_manager.get_all_storages_props(study_interface)
        st_storages_constraints = self.st_storage_manager.get_all_additional_constraints(study_interface)
        hydro_properties = self.hydro_manager.get_all_hydro_properties(study_interface)

        try:
            renewable_clusters = self.renewable_manager.get_all_renewables_props(study_interface)
        except ChildNotFoundError:  # Can happen, according to the enr-modeling
            renewable_clusters = {}

        areas = []
        for area_id, properties in area_properties.items():
            area: dict[str, Any] = {
                "id": area_id,
                "name": area_names[area_id],
                "properties": properties,
                "thermals": thermal_clusters.get(area_id, {}).values(),
                "renewables": renewable_clusters.get(area_id, {}).values(),
                "st_storages": [],
                "ui": self.area_manager.get_area_ui(study_interface, area_id),
            }

            # Hydro
            hydro_allocation = self.allocation_manager.get_allocation_for_area(study_interface, area_id)
            area["hydro"] = {
                "allocation": hydro_allocation,
                "management_options": hydro_properties[area_id].management_options,
                "inflow_structure": hydro_properties[area_id].inflow_structure,
            }

            # Short-term storages
            storage_dict = st_storages.get(area_id, {})
            for storage_id, storage in storage_dict.items():
                sts_constraints = st_storages_constraints.get(area_id, {}).get(storage_id, [])
                area["st_storages"].append({**storage.model_dump(), "constraints": sts_constraints})

            areas.append(area)

        obj["areas"] = areas

        ##########################
        # Links and BCs
        ##########################

        obj["links"] = self.links_manager.get_all_links(study_interface)
        obj["binding_constraints"] = self.binding_constraint_manager.get_binding_constraints(study_interface)

        ##########################
        # Settings
        ##########################

        obj["settings"] = {
            "time_series": self.ts_config_manager.get_timeseries_configuration(study_interface),
            "general": self.general_manager.get_general_config(study_interface),
            "advanced_parameters": self.advanced_parameters_manager.get_advanced_parameters(study_interface),
            "playlist": self.playlist_manager.get_playlist(study_interface),
            "thematic_trimming": self.thematic_trimming_manager.get_thematic_trimming(study_interface),
            "optimization": self.optimization_manager.get_optimization_preferences(study_interface),
            "adequacy_patch": self.adequacy_patch_manager.get_adequacy_patch_parameters(study_interface),
        }

        ##########################
        # Xpansion
        ##########################

        try:
            xpansion_settings = self.get_xpansion_settings(uuid)
            if xpansion_settings.additional_constraints:
                xpansion_constraint = self.xpansion_manager.get_resource_content(
                    study_interface, XpansionResourceFileType.CONSTRAINTS, xpansion_settings.additional_constraints
                )
                assert isinstance(xpansion_constraint, bytes)
                constraint_as_dict = IniReader().read(io.StringIO(xpansion_constraint.decode("utf-8")))
                constraints = []
                for constraint in constraint_as_dict.values():
                    constraint_model_args = {
                        "name": constraint.pop("name"),
                        "sign": constraint.pop("sign"),
                        "right_hand_side": constraint.pop("rhs"),
                        "candidates_coefficients": {},
                    }
                    for candidate, coefficient in constraint.items():
                        constraint_model_args["candidates_coefficients"][candidate] = coefficient
                    constraints.append(constraint_model_args)
            else:
                constraints = []

            xpansion = {
                "settings": xpansion_settings,
                "candidates": self.xpansion_manager.get_candidates(study_interface),
                "constraints": constraints,
            }

        except ChildNotFoundError:
            xpansion = None

        obj["xpansion"] = xpansion

        ##########################
        # Return the object
        ##########################

        return StudyDataDTO.model_validate(obj)

    def write_study_as_file_study(
        self, study_id: str, path: Path, with_outputs: bool = False, normalize_matrices: bool = False
    ) -> None:
        study = self.get_study(study_id)
        assert_permission(study, StudyPermissionType.READ)
        source_dao = self.get_study_interface(study).get_study_dao()

        # Create empty study on the filesystem
        study_version = StudyVersion.parse(study.version)
        assert study.name is not None
        create_new_empty_study(study_version, path, study.name, study.author or "Unknown")

        # Create the FileStudyDAO
        file_study = self.storage_service.raw_study_service.study_factory.create_from_fs(
            path, with_matrix_normalization=normalize_matrices, study_id="", use_cache=False
        )
        context = self.storage_service.variant_study_service.command_factory.command_context
        file_study_dao = FileStudyTreeDao(file_study, context.generator_matrix_constants, context.blob_service)
        # Write the given study input in the filesystem
        converter = StudyConverter(source_dao, file_study_dao, study_version, context.matrix_service)
        converter.convert_study_inputs()

        # Copy the `output` folder if asked
        output_src_path = Path(study.path) / "output"
        if with_outputs and output_src_path.exists():
            shutil.copytree(output_src_path, path / "output", dirs_exist_ok=True)
