import base64
import json
import logging
import os
from datetime import datetime, timedelta
from http import HTTPStatus
from pathlib import Path
from time import time
from typing import List, IO, Optional, cast, Union, Dict, Callable, Any
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from markupsafe import escape
from starlette.responses import FileResponse, Response

from antarest.core.config import Config
from antarest.core.exceptions import (
    StudyNotFoundError,
    StudyTypeUnsupported,
    UnsupportedOperationOnArchivedStudy,
    NotAManagedStudyException,
    CommandApplicationError,
    StudyDeletionNotAllowed,
)
from antarest.core.filetransfer.model import (
    FileDownloadTaskDTO,
)
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.interfaces.cache import ICache, CacheConstants
from antarest.core.interfaces.eventbus import IEventBus, Event, EventType
from antarest.core.jwt import JWTUser, DEFAULT_ADMIN_USER
from antarest.core.model import (
    JSON,
    PublicMode,
    StudyPermissionType,
    SUB_JSON,
)
from antarest.core.requests import (
    RequestParameters,
    UserHasNotPermissionError,
)
from antarest.core.roles import RoleType
from antarest.core.tasks.model import (
    TaskResult,
    TaskType,
    TaskListFilter,
    TaskStatus,
)
from antarest.core.tasks.service import (
    ITaskService,
    TaskUpdateNotifier,
    noop_notifier,
)
from antarest.core.utils.utils import StopWatch
from antarest.login.model import Group
from antarest.login.service import LoginService
from antarest.matrixstore.business.matrix_editor import (
    MatrixEditInstructionDTO,
)
from antarest.matrixstore.utils import parse_tsv_matrix
from antarest.study.business.area_management import (
    AreaManager,
    AreaType,
    AreaInfoDTO,
    AreaCreationDTO,
    AreaUI,
)
from antarest.study.business.binding_constraint_management import (
    BindingConstraintManager,
)
from antarest.study.business.config_management import ConfigManager
from antarest.study.business.general_management import GeneralManager
from antarest.study.business.link_management import LinkManager, LinkInfoDTO
from antarest.study.business.hydro_management import (
    HydroManager,
)
from antarest.study.business.matrix_management import MatrixManager
from antarest.study.business.playlist_management import (
    PlaylistManager,
)
from antarest.study.business.optimization_management import OptimizationManager
from antarest.study.business.advanced_parameters_management import (
    AdvancedParamsManager,
)
from antarest.study.business.table_mode_management import TableModeManager
from antarest.study.business.thematic_trimming_management import (
    ThematicTrimmingManager,
)
from antarest.study.business.timeseries_config_management import (
    TimeSeriesConfigManager,
)
from antarest.study.business.utils import execute_or_add_commands
from antarest.study.business.xpansion_management import (
    XpansionManager,
    XpansionSettingsDTO,
    XpansionCandidateDTO,
)
from antarest.study.model import (
    Study,
    StudyContentStatus,
    StudyFolder,
    DEFAULT_WORKSPACE_NAME,
    RawStudy,
    StudyMetadataPatchDTO,
    StudyMetadataDTO,
    StudyDownloadDTO,
    StudySimResultDTO,
    CommentsDto,
    STUDY_REFERENCE_TEMPLATES,
    NEW_DEFAULT_STUDY_VERSION,
    PatchStudy,
    MatrixIndex,
    PatchCluster,
    PatchArea,
    ExportFormat,
    StudyAdditionalData,
    StudyDownloadLevelDTO,
)
from antarest.study.repository import StudyMetadataRepository
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfigDTO,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    ChildNotFoundError,
)
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import (
    IniFileNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import INode
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import (
    InputSeriesMatrix,
)
from antarest.study.storage.rawstudy.model.filesystem.matrix.output_series_matrix import (
    OutputSeriesMatrix,
)
from antarest.study.storage.rawstudy.model.filesystem.raw_file_node import (
    RawFileNode,
)
from antarest.study.storage.rawstudy.raw_study_service import (
    RawStudyService,
)
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.study_download_utils import (
    StudyDownloader,
    get_output_variables_information,
)
from antarest.study.storage.utils import (
    get_default_workspace_path,
    is_managed,
    remove_from_cache,
    assert_permission,
    create_permission_from_study,
    get_start_date,
    study_matcher,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.replace_matrix import (
    ReplaceMatrix,
)
from antarest.study.storage.variantstudy.model.command.update_comments import (
    UpdateComments,
)
from antarest.study.storage.variantstudy.model.command.update_config import (
    UpdateConfig,
)
from antarest.study.storage.variantstudy.model.command.update_raw_file import (
    UpdateRawFile,
)
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy
from antarest.study.storage.variantstudy.model.model import CommandDTO
from antarest.study.storage.variantstudy.variant_study_service import (
    VariantStudyService,
)
from antarest.worker.archive_worker import ArchiveTaskArgs

logger = logging.getLogger(__name__)

MAX_MISSING_STUDY_TIMEOUT = 2  # days


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
        self.storage_service = StudyStorageService(
            raw_study_service, variant_study_service
        )
        self.user_service = user_service
        self.repository = repository
        self.event_bus = event_bus
        self.file_transfer_manager = file_transfer_manager
        self.task_service = task_service
        self.areas = AreaManager(self.storage_service, self.repository)
        self.links = LinkManager(self.storage_service)
        self.config_manager = ConfigManager(self.storage_service)
        self.general_manager = GeneralManager(self.storage_service)
        self.thematic_trimming_manager = ThematicTrimmingManager(
            self.storage_service
        )
        self.optimization_manager = OptimizationManager(self.storage_service)
        self.advanced_parameters_manager = AdvancedParamsManager(
            self.storage_service
        )
        self.hydro_manager = HydroManager(self.storage_service)
        self.ts_config_manager = TimeSeriesConfigManager(self.storage_service)
        self.table_mode_manager = TableModeManager(self.storage_service)
        self.playlist_manager = PlaylistManager(self.storage_service)
        self.xpansion_manager = XpansionManager(self.storage_service)
        self.matrix_manager = MatrixManager(self.storage_service)
        self.binding_constraint_manager = BindingConstraintManager(
            self.storage_service
        )
        self.cache_service = cache_service
        self.config = config
        self.on_deletion_callbacks: List[Callable[[str], None]] = []

    def add_on_deletion_callback(
        self, callback: Callable[[str], None]
    ) -> None:
        self.on_deletion_callbacks.append(callback)

    def _on_study_delete(self, uuid: str) -> None:
        """Run all callbacks"""
        for callback in self.on_deletion_callbacks:
            callback(uuid)

    def get(
        self,
        uuid: str,
        url: str,
        depth: int,
        formatted: bool,
        params: RequestParameters,
    ) -> JSON:
        """
        Get study data inside filesystem
        Args:
            uuid: study uuid
            url: route to follow inside study structure
            depth: depth to expand tree when route matched
            formatted: indicate if raw files must be parsed and formatted
            params: request parameters

        Returns: data study formatted in json

        """
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.READ)

        return self.storage_service.get_storage(study).get(
            study, url, depth, formatted
        )

    def get_logs(
        self,
        study_id: str,
        output_id: str,
        job_id: str,
        err_log: bool,
        params: RequestParameters,
    ) -> Optional[str]:
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
                log = cast(
                    bytes,
                    file_study.tree.get(log_location, depth=1, formatted=True),
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
        raise ChildNotFoundError(
            f"Logs for {output_id} of study {study_id} were not found"
        )

    def save_logs(
        self,
        study_id: str,
        job_id: str,
        log_suffix: str,
        log_data: str,
    ) -> None:
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

    def get_comments(
        self,
        uuid: str,
        params: RequestParameters,
    ) -> Union[str, JSON]:
        """
        Get study data inside filesystem
        Args:
            uuid: study uuid
            params: request parameters

        Returns: data study formatted in json
        """
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.READ)

        output: Union[str, JSON]
        if isinstance(study, RawStudy):
            output = self.storage_service.get_storage(study).get(
                metadata=study, url="/settings/comments", depth=-1
            )
        elif isinstance(study, VariantStudy):
            patch = self.storage_service.raw_study_service.patch_service.get(
                study
            )
            output = (
                patch.study or PatchStudy()
            ).comments or self.storage_service.get_storage(study).get(
                metadata=study, url="/settings/comments", depth=-1
            )
        else:
            raise StudyTypeUnsupported(study.id, study.type)

        try:
            # try to decode string
            output = output.decode("utf-8")  # type: ignore
        except (AttributeError, UnicodeDecodeError):
            pass

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
        elif isinstance(study, VariantStudy):
            patch = self.storage_service.raw_study_service.patch_service.get(
                study
            )
            patch_study = patch.study or PatchStudy()
            patch_study.comments = data.comments
            patch.study = patch_study
            self.storage_service.raw_study_service.patch_service.save(
                study, patch
            )
        else:
            raise StudyTypeUnsupported(study.id, study.type)

    def _get_study_metadatas(self, params: RequestParameters) -> List[Study]:
        return list(
            filter(
                lambda study: assert_permission(
                    params.user, study, StudyPermissionType.READ, raising=False
                ),
                self.repository.get_all(),
            )
        )

    def get_studies_information(
        self,
        managed: bool,
        name: Optional[str],
        workspace: Optional[str],
        folder: Optional[str],
        params: RequestParameters,
    ) -> Dict[str, StudyMetadataDTO]:
        """
        Get information for all studies.
        Args:
            managed: indicate if just managed studies should be retrieved
            name: optional name of the study to match
            folder: optional folder prefix of the study to match
            workspace: optional workspace of the study to match
            params: request parameters

        Returns: List of study information

        """
        logger.info("Fetching study listing")
        studies: Dict[str, StudyMetadataDTO] = {}
        cache_key = CacheConstants.STUDY_LISTING.value
        cached_studies = self.cache_service.get(cache_key)
        if cached_studies:
            for k in cached_studies:
                studies[k] = StudyMetadataDTO.parse_obj(cached_studies[k])
        else:
            logger.info("Retrieving all studies")
            all_studies = self.repository.get_all()
            logger.info("Studies retrieved")
            for study in all_studies:
                if not managed or is_managed(study):
                    study_metadata = self._try_get_studies_information(study)
                    if study_metadata is not None:
                        studies[study_metadata.id] = study_metadata
            self.cache_service.put(cache_key, studies)
        return {
            s.id: s
            for s in filter(
                lambda study_dto: assert_permission(
                    params.user,
                    study_dto,
                    StudyPermissionType.READ,
                    raising=False,
                )
                and study_matcher(name, workspace, folder)(study_dto)
                and (not managed or study_dto.managed),
                studies.values(),
            )
        }

    def _try_get_studies_information(
        self, study: Study
    ) -> Optional[StudyMetadataDTO]:
        try:
            return self.storage_service.get_storage(
                study
            ).get_study_information(study)
        except Exception as e:
            logger.warning(
                "Failed to build study %s (%s) metadata",
                study.id,
                study.path,
                exc_info=e,
            )
        return None

    def get_study_information(
        self, uuid: str, params: RequestParameters
    ) -> StudyMetadataDTO:
        """
        Get study information
        Args:
            uuid: study uuid
            params: request parameters

        Returns: study information

        """
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.READ)
        logger.info(
            "study %s metadata asked by user %s", uuid, params.get_user_id()
        )
        # todo debounce this with a "update_study_last_access" method updating only every some seconds
        study.last_access = datetime.utcnow()
        self.repository.save(study, update_in_listing=False)
        return self.storage_service.get_storage(study).get_study_information(
            study
        )

    def invalidate_cache_listing(self, params: RequestParameters) -> None:
        if params.user and params.user.is_site_admin():
            self.cache_service.invalidate(CacheConstants.STUDY_LISTING.value)
        else:
            logger.error(f"User {params.user} is not site admin")
            raise UserHasNotPermissionError()

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
        assert_permission(params.user, study, StudyPermissionType.READ)

        if metadata_patch.horizon:
            study_settings_url = "settings/generaldata/general"
            self._assert_study_unarchived(study)
            study_settings = self.storage_service.get_storage(study).get(
                study, study_settings_url
            )
            study_settings["horizon"] = metadata_patch.horizon

            self._edit_study_using_command(
                study=study, url=study_settings_url, data=study_settings
            )
        if metadata_patch.author:
            study_antares_url = "study/antares"
            self._assert_study_unarchived(study)
            study_antares = self.storage_service.get_storage(study).get(
                study, study_antares_url
            )
            study_antares["author"] = metadata_patch.author

            self._edit_study_using_command(
                study=study, url=study_antares_url, data=study_antares
            )
        study.additional_data = study.additional_data or StudyAdditionalData()
        if metadata_patch.name:
            study.name = metadata_patch.name
        if metadata_patch.author:
            study.additional_data.author = metadata_patch.author
        if metadata_patch.horizon:
            study.additional_data.horizon = metadata_patch.horizon

        new_metadata = self.storage_service.get_storage(
            study
        ).patch_update_study_metadata(study, metadata_patch)

        self.event_bus.push(
            Event(
                type=EventType.STUDY_DATA_EDITED,
                payload=study.to_json_summary(),
                permissions=create_permission_from_study(study),
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

        logger.info(
            "study %s path asked by user %s", uuid, params.get_user_id()
        )
        return self.storage_service.get_storage(study).get_study_path(study)

    def create_study(
        self,
        study_name: str,
        version: Optional[str],
        group_ids: List[str],
        params: RequestParameters,
    ) -> str:
        """
        Create empty study
        Args:
            study_name: study name to set
            version: version number of the study to create
            group_ids: group to link to study
            params: request parameters

        Returns: new study uuid

        """
        sid = str(uuid4())
        study_path = str(get_default_workspace_path(self.config) / sid)

        raw = RawStudy(
            id=sid,
            name=study_name,
            workspace=DEFAULT_WORKSPACE_NAME,
            path=study_path,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            version=version or NEW_DEFAULT_STUDY_VERSION,
            additional_data=StudyAdditionalData(),
        )

        raw = self.storage_service.raw_study_service.create(raw)
        self._save_study(raw, params.user, group_ids)
        self.event_bus.push(
            Event(
                type=EventType.STUDY_CREATED,
                payload=raw.to_json_summary(),
                permissions=create_permission_from_study(raw),
            )
        )

        logger.info(
            "study %s created by user %s", raw.id, params.get_user_id()
        )
        return str(raw.id)

    def get_study_synthesis(
        self, study_id: str, params: RequestParameters
    ) -> FileStudyTreeConfigDTO:
        """
        Return study synthesis
        Args:
            study_id: study id
            params: request parameters

        Returns: study synthesis

        """
        study = self.get_study(study_id)
        assert_permission(params.user, study, StudyPermissionType.READ)
        study.last_access = datetime.utcnow()
        self.repository.save(study, update_in_listing=False)
        return self.storage_service.get_storage(study).get_synthesis(
            study, params
        )

    def get_input_matrix_startdate(
        self, study_id: str, path: Optional[str], params: RequestParameters
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
            if isinstance(data_node, OutputSeriesMatrix) or isinstance(
                data_node, InputSeriesMatrix
            ):
                level = StudyDownloadLevelDTO(data_node.freq)
        return get_start_date(file_study, output_id, level)

    def remove_duplicates(self) -> None:
        study_paths: Dict[str, List[str]] = {}
        for study in self.repository.get_all():
            if isinstance(study, RawStudy) and not study.archived:
                path = str(study.path)
                if not path in study_paths:
                    study_paths[path] = []
                study_paths[path].append(study.id)

        for studies_with_same_path in study_paths.values():
            if len(studies_with_same_path) > 1:
                logger.info(
                    f"Found studies {studies_with_same_path} with same path, de duplicating"
                )
                for study_name in studies_with_same_path[1:]:
                    logger.info(f"Removing study {study_name}")
                    self.repository.delete(study_name)

    def sync_studies_on_disk(
        self, folders: List[StudyFolder], directory: Optional[Path] = None
    ) -> None:
        """
        Used by watcher to send list of studies present on filesystem.

        Args:
            folders: list of studies currently present on folder
            directory: directory of studies that will be watched

        Returns:

        """
        now = datetime.utcnow()
        clean_up_missing_studies_threshold = now - timedelta(
            days=MAX_MISSING_STUDY_TIMEOUT
        )
        all_studies = self.repository.get_all_raw()
        if directory:
            all_studies = [
                raw_study
                for raw_study in all_studies
                if directory in Path(raw_study.path).parents
            ]
        studies_by_path = {study.path: study for study in all_studies}

        # delete orphan studies on database
        paths = [str(f.path) for f in folders]
        for study in all_studies:
            if (
                isinstance(study, RawStudy)
                and not study.archived
                and (
                    study.workspace != DEFAULT_WORKSPACE_NAME
                    and study.path not in paths
                )
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
                elif study.missing < clean_up_missing_studies_threshold:
                    logger.info(
                        "Study %s at %s is not present in disk and will be deleted",
                        study.id,
                        study.path,
                    )
                    self.event_bus.push(
                        Event(
                            type=EventType.STUDY_DELETED,
                            payload=study.to_json_summary(),
                            permissions=create_permission_from_study(study),
                        )
                    )
                    self.repository.delete(study.id)

        # Add new studies
        study_paths = [
            study.path for study in all_studies if study.missing is None
        ]
        missing_studies = {
            study.path: study
            for study in all_studies
            if study.missing is not None
        }
        for folder in folders:
            study_path = str(folder.path)
            if study_path not in study_paths:
                try:
                    if study_path not in missing_studies.keys():
                        base_path = self.config.storage.workspaces[
                            folder.workspace
                        ].path
                        dir_name = folder.path.relative_to(base_path)
                        study = RawStudy(
                            id=str(uuid4()),
                            name=folder.path.name,
                            path=study_path,
                            folder=str(dir_name),
                            workspace=folder.workspace,
                            owner=None,
                            groups=folder.groups,
                            public_mode=PublicMode.FULL
                            if len(folder.groups) == 0
                            else PublicMode.NONE,
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

                    self.storage_service.raw_study_service.update_from_raw_meta(
                        study, fallback_on_default=True
                    )

                    logger.warning("Skipping study format error analysis")
                    # TODO re enable this on an async worker
                    # study.content_status = self._analyse_study(study)

                    self.repository.save(study)
                    self.event_bus.push(
                        Event(
                            type=EventType.STUDY_CREATED,
                            payload=study.to_json_summary(),
                            permissions=create_permission_from_study(study),
                        )
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to add study {folder.path}", exc_info=e
                    )
            elif directory and study_path in studies_by_path:
                existing_study = studies_by_path[study_path]
                if self.storage_service.raw_study_service.update_name_and_version_from_raw_meta(
                    existing_study
                ):
                    self.repository.save(existing_study)

    def copy_study(
        self,
        src_uuid: str,
        dest_study_name: str,
        group_ids: List[str],
        use_task: bool,
        params: RequestParameters,
        with_outputs: bool = False,
    ) -> str:
        """
        Copy study to an other location.

        Args:
            src_uuid: source study
            dest_study_name: destination study
            group_ids: group to attach on new study
            params: request parameters
            with_outputs: indicate if outputs should be copied too
            use_task: indicate if the task job service should be used

        Returns:

        """
        src_study = self.get_study(src_uuid)
        assert_permission(params.user, src_study, StudyPermissionType.READ)
        self._assert_study_unarchived(src_study)

        def copy_task(notifier: TaskUpdateNotifier) -> TaskResult:
            origin_study = self.get_study(src_uuid)
            study = self.storage_service.get_storage(origin_study).copy(
                origin_study,
                dest_study_name,
                with_outputs,
            )
            self._save_study(study, params.user, group_ids)
            self.event_bus.push(
                Event(
                    type=EventType.STUDY_CREATED,
                    payload=study.to_json_summary(),
                    permissions=create_permission_from_study(study),
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

    def move_study(
        self, study_id: str, new_folder: str, params: RequestParameters
    ) -> None:
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
                permissions=create_permission_from_study(study),
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
                self.storage_service.get_storage(target_study).export_study(
                    target_study, export_path, outputs
                )
                self.file_transfer_manager.set_ready(export_id)
                return TaskResult(
                    success=True, message=f"Study {uuid} successfully exported"
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

        return FileDownloadTaskDTO(
            file=export_file_download.to_dto(), task=task_id
        )

    def output_variables_information(
        self,
        study_uuid: str,
        output_uuid: str,
        params: RequestParameters,
    ) -> Dict[str, List[str]]:
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
        return get_output_variables_information(
            self.storage_service.get_storage(study).get_raw(study), output_uuid
        )

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

        return FileDownloadTaskDTO(
            file=export_file_download.to_dto(), task=task_id
        )

    def export_study_flat(
        self,
        uuid: str,
        params: RequestParameters,
        dest: Path,
        output_list: Optional[List[str]] = None,
    ) -> None:
        logger.info(f"Flat exporting study {uuid}")
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.READ)
        self._assert_study_unarchived(study)

        return self.storage_service.get_storage(study).export_study_flat(
            study, dest, len(output_list or []) > 0, output_list
        )

    def delete_study(
        self, uuid: str, children: bool, params: RequestParameters
    ) -> None:
        """
        Delete study
        Args:
            uuid: study uuid
            params: request parameters

        Returns:

        """
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.DELETE)

        study_info = study.to_json_summary()

        # this prefetch the workspace because it is lazy loaded and the object is deleted before using workspace attribute in raw study deletion
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
                raise StudyDeletionNotAllowed(
                    study.id, "Study has variant children"
                )

        self.repository.delete(study.id)

        self.event_bus.push(
            Event(
                type=EventType.STUDY_DELETED,
                payload=study_info,
                permissions=create_permission_from_study(study),
            )
        )

        # delete the files afterward for
        # if the study cannot be deleted from database for foreign key reason
        if self._assert_study_unarchived(study=study, raise_exception=False):
            self.storage_service.get_storage(study).delete(study)
        else:
            if isinstance(study, RawStudy):
                os.unlink(
                    self.storage_service.raw_study_service.get_archive_path(
                        study
                    )
                )

        logger.info("study %s deleted by user %s", uuid, params.get_user_id())

        self._on_study_delete(uuid=uuid)

    def delete_output(
        self, uuid: str, output_name: str, params: RequestParameters
    ) -> None:
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
        self.storage_service.get_storage(study).delete_output(
            study, output_name
        )
        self.event_bus.push(
            Event(
                type=EventType.STUDY_DATA_EDITED,
                payload=study.to_json_summary(),
                permissions=create_permission_from_study(study),
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
        tmp_export_file: Optional[Path] = None,
    ) -> Union[Response, FileDownloadTaskDTO, FileResponse]:
        """
        Download outputs
        Args:
            study_id: study Id
            output_id: output id
            data: Json parameters
            use_task: use task or not
            filetype: type of returning file,
            tmp_export_file: temporary file (if use_task is false),
            params: request parameters

        Returns: CSV content file

        """
        # GET STUDY ID
        study = self.get_study(study_id)
        assert_permission(params.user, study, StudyPermissionType.READ)
        self._assert_study_unarchived(study)
        logger.info(
            f"Study {study_id} output download asked by {params.get_user_id()}",
        )

        if use_task:
            logger.info(f"Exporting {output_id} from study {study_id}")
            export_name = (
                f"Study filtered output {study.name}/{output_id} export"
            )
            export_file_download = self.file_transfer_manager.request_download(
                f"{study.name}-{study_id}-{output_id}_filtered.{'tar.gz' if filetype == ExportFormat.TAR_GZ else 'zip'}",
                export_name,
                params.user,
            )
            export_path = Path(export_file_download.path)
            export_id = export_file_download.id

            def export_task(notifier: TaskUpdateNotifier) -> TaskResult:
                try:
                    study = self.get_study(study_id)
                    stopwatch = StopWatch()
                    matrix = StudyDownloader.build(
                        self.storage_service.get_storage(study).get_raw(study),
                        output_id,
                        data,
                    )
                    stopwatch.log_elapsed(
                        lambda x: logger.info(
                            f"Study {study_id} filtered output {output_id} built in {x}s"
                        )
                    )
                    StudyDownloader.export(matrix, filetype, export_path)
                    stopwatch.log_elapsed(
                        lambda x: logger.info(
                            f"Study {study_id} filtered output {output_id} exported in {x}s"
                        )
                    )
                    self.file_transfer_manager.set_ready(export_id)
                    return TaskResult(
                        success=True,
                        message=f"Study filtered output {study_id}/{output_id} successfully exported",
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

            return FileDownloadTaskDTO(
                file=export_file_download.to_dto(), task=task_id
            )
        else:
            stopwatch = StopWatch()
            matrix = StudyDownloader.build(
                self.storage_service.get_storage(study).get_raw(study),
                output_id,
                data,
            )
            stopwatch.log_elapsed(
                lambda x: logger.info(
                    f"Study {study_id} filtered output {output_id} built in {x}s"
                )
            )
            if tmp_export_file is not None:
                StudyDownloader.export(matrix, filetype, tmp_export_file)
                stopwatch.log_elapsed(
                    lambda x: logger.info(
                        f"Study {study_id} filtered output {output_id} exported in {x}s"
                    )
                )
                return FileResponse(
                    tmp_export_file,
                    headers={"Content-Disposition": "inline"}
                    if filetype == ExportFormat.JSON
                    else {
                        "Content-Disposition": f'attachment; filename="output-{output_id}.{"tar.gz" if filetype == ExportFormat.TAR_GZ else "zip"}'
                    },
                    media_type=filetype,
                )
            else:
                json_response = json.dumps(
                    matrix.dict(),
                    ensure_ascii=False,
                    allow_nan=True,
                    indent=None,
                    separators=(",", ":"),
                ).encode("utf-8")
                return Response(
                    content=json_response, media_type="application/json"
                )

    def get_study_sim_result(
        self, study_id: str, params: RequestParameters
    ) -> List[StudySimResultDTO]:
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

        return self.storage_service.get_storage(study).get_study_sim_result(
            study
        )

    def set_sim_reference(
        self,
        study_id: str,
        output_id: str,
        status: bool,
        params: RequestParameters,
    ) -> None:
        """
        Set simulation as the reference output
        Args:
            study_id: study Id
            output_id: output id
            status: state of the reference status
            params: request parameters

        Returns: None

        """
        study = self.get_study(study_id)
        assert_permission(params.user, study, StudyPermissionType.WRITE)
        self._assert_study_unarchived(study)

        logger.info(
            "output %s set by user %s as reference (%b) for study %s",
            output_id,
            params.get_user_id(),
            status,
            study_id,
        )

        self.storage_service.get_storage(study).set_reference_output(
            study, output_id, status
        )

    def import_study(
        self,
        stream: IO[bytes],
        group_ids: List[str],
        params: RequestParameters,
    ) -> str:
        """
        Import zipped study.

        Args:
            stream: zip file
            group_ids: group to attach to study
            params: request parameters

        Returns: new study uuid

        """
        sid = str(uuid4())
        path = str(get_default_workspace_path(self.config) / sid)
        study = RawStudy(
            id=sid,
            workspace=DEFAULT_WORKSPACE_NAME,
            path=path,
            additional_data=StudyAdditionalData(),
        )
        study = self.storage_service.raw_study_service.import_study(
            study, stream
        )
        study.updated_at = datetime.utcnow()

        # status = self._analyse_study(study)
        self._save_study(
            study,
            owner=params.user,
            group_ids=group_ids,
            #    content_status=status,
        )
        self.event_bus.push(
            Event(
                type=EventType.STUDY_CREATED,
                payload=study.to_json_summary(),
                permissions=create_permission_from_study(study),
            )
        )

        logger.info(
            "study %s imported by user %s", study.id, params.get_user_id()
        )
        return str(study.id)

    def import_output(
        self,
        uuid: str,
        output: Union[IO[bytes], Path],
        params: RequestParameters,
        output_name_suffix: Optional[str] = None,
        auto_unzip: bool = True,
    ) -> Optional[str]:
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
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.RUN)
        self._assert_study_unarchived(study)
        if not Path(study.path).exists():
            raise StudyNotFoundError(
                f"Study files were not found for study {uuid}"
            )

        output_id = self.storage_service.get_storage(study).import_output(
            study, output, output_name_suffix
        )
        remove_from_cache(cache=self.cache_service, root_id=study.id)
        logger.info(
            "output added to study %s by user %s", uuid, params.get_user_id()
        )

        if (
            output_id
            and isinstance(output, Path)
            and output.suffix == ".zip"
            and auto_unzip
        ):
            self.unarchive_output(
                uuid, output_id, not is_managed(study), params
            )

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
        if isinstance(tree_node, IniFileNode):
            return UpdateConfig(
                target=url,
                data=data,
                command_context=self.storage_service.variant_study_service.command_factory.command_context,
            )
        elif isinstance(tree_node, InputSeriesMatrix):
            return ReplaceMatrix(
                target=url,
                matrix=parse_tsv_matrix(data)
                if isinstance(data, bytes)
                else data,
                command_context=self.storage_service.variant_study_service.command_factory.command_context,
            )
        elif isinstance(tree_node, RawFileNode):
            if url.split("/")[-1] == "comments":
                return UpdateComments(
                    target=url,
                    comments=data,
                    command_context=self.storage_service.variant_study_service.command_factory.command_context,
                )
            elif isinstance(data, bytes):
                return UpdateRawFile(
                    target=url,
                    b64Data=base64.b64encode(data).decode("utf-8"),
                    command_context=self.storage_service.variant_study_service.command_factory.command_context,
                )
        raise NotImplementedError()

    def _edit_study_using_command(
        self, study: Study, url: str, data: SUB_JSON
    ) -> ICommand:
        """
        Replace data on disk with new, using ICommand
        Args:
            study: study
            url: data path to reach
            data: new data to replace
        """

        study_service = self.storage_service.get_storage(study)
        file_study = study_service.get_raw(metadata=study)
        tree_node = file_study.tree.get_node(url.split("/"))

        command = self._create_edit_study_command(
            tree_node=tree_node, url=url, data=data
        )
        if isinstance(study_service, RawStudyService):
            res = command.apply(study_data=file_study)
            if not is_managed(study):
                tree_node.denormalize()
            if not res.status:
                raise CommandApplicationError(res.message)

            lastsave_url = "study/antares/lastsave"
            lastsave_node = file_study.tree.get_node(lastsave_url.split("/"))
            self._create_edit_study_command(
                tree_node=lastsave_node, url=lastsave_url, data=int(time())
            ).apply(file_study)
            self.storage_service.variant_study_service.invalidate_cache(study)

        elif isinstance(study_service, VariantStudyService):
            study_service.append_command(
                study_id=file_study.config.study_id,
                command=command.to_dto(),
                params=RequestParameters(user=DEFAULT_ADMIN_USER),
            )
        else:
            raise NotImplementedError()
        return command  # for testing purpose

    def apply_commands(
        self, uuid: str, commands: List[CommandDTO], params: RequestParameters
    ) -> Optional[List[str]]:
        study = self.get_study(uuid)
        if isinstance(study, VariantStudy):
            return self.storage_service.variant_study_service.append_commands(
                uuid, commands, params
            )
        else:
            file_study = self.storage_service.raw_study_service.get_raw(study)
            assert_permission(params.user, study, StudyPermissionType.WRITE)
            self._assert_study_unarchived(study)
            parsed_commands: List[ICommand] = []
            for command in commands:
                parsed_commands.extend(
                    self.storage_service.variant_study_service.command_factory.to_icommand(
                        command
                    )
                )
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
                permissions=create_permission_from_study(study),
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
    ) -> JSON:
        """
        Replace data inside study.

        Args:
            uuid: study id
            url: path data target in study
            new: new data to replace
            params: request parameters

        Returns: new data replaced

        """
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.WRITE)
        self._assert_study_unarchived(study)

        self._edit_study_using_command(
            study=study, url=url.strip().strip("/"), data=new
        )

        self.event_bus.push(
            Event(
                type=EventType.STUDY_DATA_EDITED,
                payload=study.to_json_summary(),
                permissions=create_permission_from_study(study),
            )
        )
        logger.info(
            "data %s on study %s updated by user %s",
            url,
            uuid,
            params.get_user_id(),
        )
        return cast(JSON, new)

    def change_owner(
        self, study_id: str, owner_id: int, params: RequestParameters
    ) -> None:
        """
        Change study owner
        Args:
            study_id: study uuid
            owner_id: new owner id
            params: request parameters

        Returns:

        """
        study = self.get_study(study_id)
        assert_permission(
            params.user, study, StudyPermissionType.MANAGE_PERMISSIONS
        )
        self._assert_study_unarchived(study)
        new_owner = self.user_service.get_user(owner_id, params)
        study.owner = new_owner
        self.repository.save(study)
        self.event_bus.push(
            Event(
                type=EventType.STUDY_EDITED,
                payload=study.to_json_summary(),
                permissions=create_permission_from_study(study),
            )
        )

        self._edit_study_using_command(
            study=study,
            url="study/antares/author",
            data=new_owner.name if new_owner is not None else None,
        )

        logger.info(
            "user %s change study %s owner to %d",
            params.get_user_id(),
            study_id,
            owner_id,
        )

    def add_group(
        self, study_id: str, group_id: str, params: RequestParameters
    ) -> None:
        """
        Attach new group on study.

        Args:
            study_id: study uuid
            group_id: group id to attach
            params: request parameters

        Returns:

        """
        study = self.get_study(study_id)
        assert_permission(
            params.user, study, StudyPermissionType.MANAGE_PERMISSIONS
        )
        group = self.user_service.get_group(group_id, params)
        if group not in study.groups:
            study.groups = study.groups + [group]
        self.repository.save(study)
        self.event_bus.push(
            Event(
                type=EventType.STUDY_EDITED,
                payload=study.to_json_summary(),
                permissions=create_permission_from_study(study),
            )
        )

        logger.info(
            "adding group %s to study %s by user %s",
            group_id,
            study_id,
            params.get_user_id(),
        )

    def remove_group(
        self, study_id: str, group_id: str, params: RequestParameters
    ) -> None:
        """
        Detach group on study
        Args:
            study_id: study uuid
            group_id: group to detach
            params: request parameters

        Returns:

        """
        study = self.get_study(study_id)
        assert_permission(
            params.user, study, StudyPermissionType.MANAGE_PERMISSIONS
        )
        study.groups = [
            group for group in study.groups if group.id != group_id
        ]
        self.repository.save(study)
        self.event_bus.push(
            Event(
                type=EventType.STUDY_EDITED,
                payload=study.to_json_summary(),
                permissions=create_permission_from_study(study),
            )
        )

        logger.info(
            "removing group %s to study %s by user %s",
            group_id,
            study_id,
            params.get_user_id(),
        )

    def set_public_mode(
        self, study_id: str, mode: PublicMode, params: RequestParameters
    ) -> None:
        """
        Update public mode permission on study
        Args:
            study_id: study uuid
            mode: new public permission
            params: request parameters

        Returns:

        """
        study = self.get_study(study_id)
        assert_permission(
            params.user, study, StudyPermissionType.MANAGE_PERMISSIONS
        )
        study.public_mode = mode
        self.repository.save(study)
        self.event_bus.push(
            Event(
                type=EventType.STUDY_EDITED,
                payload=study.to_json_summary(),
                permissions=create_permission_from_study(study),
            )
        )
        logger.info(
            "updated public mode of study %s by user %s",
            study_id,
            params.get_user_id(),
        )

    def check_errors(self, uuid: str) -> List[str]:
        study = self.get_study(uuid)
        self._assert_study_unarchived(study)
        return self.storage_service.raw_study_service.check_errors(study)

    def get_all_areas(
        self,
        uuid: str,
        area_type: Optional[AreaType],
        ui: bool,
        params: RequestParameters,
    ) -> Union[List[AreaInfoDTO], Dict[str, Any]]:
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.READ)
        return (
            self.areas.get_all_areas_ui_info(study)
            if ui
            else self.areas.get_all_areas(study, area_type)
        )

    def get_all_links(
        self,
        uuid: str,
        with_ui: bool,
        params: RequestParameters,
    ) -> List[LinkInfoDTO]:
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
                permissions=create_permission_from_study(study),
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
                permissions=create_permission_from_study(study),
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
        updated_area = self.areas.update_area_metadata(
            study, area_id, area_patch_dto
        )
        self.event_bus.push(
            Event(
                type=EventType.STUDY_DATA_EDITED,
                payload=study.to_json_summary(),
                permissions=create_permission_from_study(study),
            )
        )
        return updated_area

    def update_area_ui(
        self,
        uuid: str,
        area_id: str,
        area_ui: AreaUI,
        params: RequestParameters,
    ) -> None:
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.WRITE)
        self._assert_study_unarchived(study)
        return self.areas.update_area_ui(study, area_id, area_ui)

    def update_thermal_cluster_metadata(
        self,
        uuid: str,
        area_id: str,
        clusters_metadata: Dict[str, PatchCluster],
        params: RequestParameters,
    ) -> AreaInfoDTO:
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.WRITE)
        self._assert_study_unarchived(study)
        return self.areas.update_thermal_cluster_metadata(
            study, area_id, clusters_metadata
        )

    def delete_area(
        self, uuid: str, area_id: str, params: RequestParameters
    ) -> None:
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.WRITE)
        self._assert_study_unarchived(study)
        self.areas.delete_area(study, area_id)
        self.event_bus.push(
            Event(
                type=EventType.STUDY_DATA_EDITED,
                payload=study.to_json_summary(),
                permissions=create_permission_from_study(study),
            )
        )

    def delete_link(
        self,
        uuid: str,
        area_from: str,
        area_to: str,
        params: RequestParameters,
    ) -> None:
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.WRITE)
        self._assert_study_unarchived(study)
        self.links.delete_link(study, area_from, area_to)
        self.event_bus.push(
            Event(
                type=EventType.STUDY_DATA_EDITED,
                payload=study.to_json_summary(),
                permissions=create_permission_from_study(study),
            )
        )

    def archive(self, uuid: str, params: RequestParameters) -> str:
        logger.info(f"Archiving study {uuid}")
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.DELETE)

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
            raise HTTPException(
                HTTPStatus.BAD_REQUEST, "Study is already archiving"
            )

        def archive_task(notifier: TaskUpdateNotifier) -> TaskResult:
            study_to_archive = self.get_study(uuid)
            archived_path = self.storage_service.raw_study_service.archive(
                study_to_archive
            )
            study_to_archive.archived = True
            self.repository.save(study_to_archive)
            self.event_bus.push(
                Event(
                    type=EventType.STUDY_EDITED,
                    payload=study_to_archive.to_json_summary(),
                    permissions=create_permission_from_study(study_to_archive),
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
            raise HTTPException(
                HTTPStatus.BAD_REQUEST, "Study is not archived"
            )

        if self.task_service.list_tasks(
            TaskListFilter(
                ref_id=uuid,
                type=[TaskType.UNARCHIVE, TaskType.ARCHIVE],
                status=[TaskStatus.RUNNING, TaskStatus.PENDING],
            ),
            RequestParameters(user=DEFAULT_ADMIN_USER),
        ):
            raise HTTPException(
                HTTPStatus.BAD_REQUEST, "Study is already unarchiving"
            )

        assert_permission(params.user, study, StudyPermissionType.DELETE)

        if not isinstance(study, RawStudy):
            raise StudyTypeUnsupported(study.id, study.type)

        def unarchive_task(notifier: TaskUpdateNotifier) -> TaskResult:
            study_to_archive = self.get_study(uuid)
            self.storage_service.raw_study_service.unarchive(study_to_archive)
            study_to_archive.archived = False

            os.unlink(
                self.storage_service.raw_study_service.get_archive_path(
                    study_to_archive
                )
            )
            self.repository.save(study_to_archive)
            self.event_bus.push(
                Event(
                    type=EventType.STUDY_EDITED,
                    payload=study.to_json_summary(),
                    permissions=create_permission_from_study(study),
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
        owner: Optional[JWTUser] = None,
        group_ids: List[str] = list(),
        content_status: StudyContentStatus = StudyContentStatus.VALID,
    ) -> None:
        """
        Create new study with owner, group or content_status.
        Args:
            study: study to save
            owner: new owner
            group_ids: groups to attach
            content_status: new content_status

        Returns:

        """
        if not owner:
            raise UserHasNotPermissionError

        if isinstance(study, RawStudy):
            study.content_status = content_status

        if owner:
            study.owner = self.user_service.get_user(
                owner.impersonator, params=RequestParameters(user=owner)
            )
            groups = []
            for gid in group_ids:
                group = next(filter(lambda g: g.id == gid, owner.groups), None)
                if (
                    group is None
                    or not group.role.is_higher_or_equals(RoleType.WRITER)
                    and not owner.is_site_admin()
                ):
                    raise UserHasNotPermissionError()
                groups.append(Group(id=group.id, name=group.name))
            study.groups = groups

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

    def _assert_study_unarchived(
        self, study: Study, raise_exception: bool = True
    ) -> bool:
        if study.archived and raise_exception:
            raise UnsupportedOperationOnArchivedStudy(study.id)
        return not study.archived

    def _analyse_study(self, metadata: Study) -> StudyContentStatus:
        """
        Analyze study integrity
        Args:
            metadata: study to analyze

        Returns: VALID if study has any integrity mistakes.
        WARNING if studies has mistakes.
        ERROR if tree was not able to analyse structuree without raise error.

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

    @staticmethod
    def get_studies_versions(params: RequestParameters) -> List[str]:
        return list(STUDY_REFERENCE_TEMPLATES.keys())

    def create_xpansion_configuration(
        self,
        uuid: str,
        zipped_config: Optional[UploadFile],
        params: RequestParameters,
    ) -> None:
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.WRITE)
        self._assert_study_unarchived(study)
        self.xpansion_manager.create_xpansion_configuration(
            study, zipped_config
        )

    def delete_xpansion_configuration(
        self, uuid: str, params: RequestParameters
    ) -> None:
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.WRITE)
        self._assert_study_unarchived(study)
        self.xpansion_manager.delete_xpansion_configuration(study)

    def get_xpansion_settings(
        self, uuid: str, params: RequestParameters
    ) -> XpansionSettingsDTO:
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.READ)
        return self.xpansion_manager.get_xpansion_settings(study)

    def update_xpansion_settings(
        self,
        uuid: str,
        xpansion_settings_dto: XpansionSettingsDTO,
        params: RequestParameters,
    ) -> XpansionSettingsDTO:
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.READ)
        self._assert_study_unarchived(study)
        return self.xpansion_manager.update_xpansion_settings(
            study, xpansion_settings_dto
        )

    def add_candidate(
        self,
        uuid: str,
        xpansion_candidate_dto: XpansionCandidateDTO,
        params: RequestParameters,
    ) -> None:
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.WRITE)
        self._assert_study_unarchived(study)
        return self.xpansion_manager.add_candidate(
            study, xpansion_candidate_dto
        )

    def get_candidate(
        self, uuid: str, candidate_name: str, params: RequestParameters
    ) -> XpansionCandidateDTO:
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.READ)
        return self.xpansion_manager.get_candidate(study, candidate_name)

    def get_candidates(
        self, uuid: str, params: RequestParameters
    ) -> List[XpansionCandidateDTO]:
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
        return self.xpansion_manager.update_candidate(
            study, candidate_name, xpansion_candidate_dto
        )

    def delete_xpansion_candidate(
        self, uuid: str, candidate_name: str, params: RequestParameters
    ) -> None:
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.READ)
        self._assert_study_unarchived(study)
        return self.xpansion_manager.delete_candidate(study, candidate_name)

    def update_xpansion_constraints_settings(
        self,
        uuid: str,
        constraints_file_name: Optional[str],
        params: RequestParameters,
    ) -> None:
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.WRITE)
        self._assert_study_unarchived(study)
        return self.xpansion_manager.update_xpansion_constraints_settings(
            study, constraints_file_name
        )

    def update_matrix(
        self,
        uuid: str,
        path: str,
        matrix_edit_instruction: List[MatrixEditInstructionDTO],
        params: RequestParameters,
    ) -> None:
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.WRITE)
        self._assert_study_unarchived(study)
        self.matrix_manager.update_matrix(study, path, matrix_edit_instruction)

    def check_and_update_all_study_versions_in_database(
        self, params: RequestParameters
    ) -> None:
        if params.user and not params.user.is_site_admin():
            logger.error(f"User {params.user.id} is not site admin")
            raise UserHasNotPermissionError()
        studies = self.repository.get_all()
        for study in studies:
            if isinstance(study, RawStudy) and not is_managed(study):
                storage = self.storage_service.raw_study_service
                storage.check_and_update_study_version_in_database(study)

    def archive_outputs(
        self, study_id: str, params: RequestParameters
    ) -> None:
        logger.info(f"Archiving all outputs for study {study_id}")
        study = self.get_study(study_id)
        assert_permission(params.user, study, StudyPermissionType.WRITE)
        self._assert_study_unarchived(study)
        study = self.get_study(study_id)
        file_study = self.storage_service.get_storage(study).get_raw(study)
        for output in file_study.config.outputs:
            if not file_study.config.outputs[output].archived:
                self.archive_output(study_id, output, params)

    def archive_output(
        self,
        study_id: str,
        output_id: str,
        params: RequestParameters,
        force: bool = False,
    ) -> Optional[str]:
        study = self.get_study(study_id)
        assert_permission(params.user, study, StudyPermissionType.WRITE)
        self._assert_study_unarchived(study)

        if not force and self.task_service.list_tasks(
            TaskListFilter(
                ref_id=study_id,
                type=[TaskType.UNARCHIVE, TaskType.ARCHIVE],
                status=[TaskStatus.RUNNING, TaskStatus.PENDING],
            ),
            RequestParameters(user=DEFAULT_ADMIN_USER),
        ):
            raise HTTPException(
                HTTPStatus.BAD_REQUEST, "Study output is already (un)archiving"
            )

        task_name = f"Archive output {study_id}/{output_id}"

        def archive_output_task(
            notifier: TaskUpdateNotifier,
        ) -> TaskResult:
            try:
                study = self.get_study(study_id)
                stopwatch = StopWatch()
                self.storage_service.get_storage(study).archive_study_output(
                    study, output_id
                )
                stopwatch.log_elapsed(
                    lambda x: logger.info(
                        f"Output {output_id} of study {study_id} archived in {x}s"
                    )
                )
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
    ) -> Optional[str]:
        study = self.get_study(study_id)
        assert_permission(params.user, study, StudyPermissionType.WRITE)
        self._assert_study_unarchived(study)

        if self.task_service.list_tasks(
            TaskListFilter(
                ref_id=study_id,
                type=[TaskType.UNARCHIVE, TaskType.ARCHIVE],
                status=[TaskStatus.RUNNING, TaskStatus.PENDING],
            ),
            RequestParameters(user=DEFAULT_ADMIN_USER),
        ):
            raise HTTPException(
                HTTPStatus.BAD_REQUEST, "Study output is already (un)archiving"
            )

        task_name = f"Unarchive output {study.name}/{output_id} ({study_id})"

        def unarchive_output_task(
            notifier: TaskUpdateNotifier,
        ) -> TaskResult:
            try:
                study = self.get_study(study_id)
                stopwatch = StopWatch()
                self.storage_service.get_storage(study).unarchive_study_output(
                    study, output_id, keep_src_zip
                )
                stopwatch.log_elapsed(
                    lambda x: logger.info(
                        f"Output {output_id} of study {study_id} unarchived in {x}s"
                    )
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
