import base64
import io
import logging
import os
import shutil
from datetime import datetime
from http import HTTPStatus
from pathlib import Path
from time import time
from typing import List, IO, Optional, cast, Union, Dict, Callable
from uuid import uuid4

from fastapi import HTTPException
from markupsafe import escape

from antarest.core.config import Config
from antarest.core.filetransfer.model import (
    FileDownloadTaskDTO,
)
from antarest.core.filetransfer.service import FileTransferManager
from antarest.core.exceptions import (
    StudyNotFoundError,
    StudyTypeUnsupported,
    UnsupportedOperationOnArchivedStudy,
    NotAManagedStudyException,
    CommandApplicationError,
)
from antarest.core.interfaces.cache import ICache, CacheConstants
from antarest.core.interfaces.eventbus import IEventBus, Event, EventType
from antarest.core.jwt import JWTUser, DEFAULT_ADMIN_USER
from antarest.core.model import JSON, PublicMode, StudyPermissionType, SUB_JSON
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
from antarest.login.model import Group
from antarest.login.service import LoginService
from antarest.matrixstore.utils import parse_tsv_matrix
from antarest.study.business.area_management import (
    AreaManager,
    AreaType,
    AreaInfoDTO,
    AreaCreationDTO,
    AreaUI,
)
from antarest.study.business.link_management import LinkManager, LinkInfoDTO
from antarest.study.model import (
    Study,
    StudyContentStatus,
    StudyFolder,
    DEFAULT_WORKSPACE_NAME,
    RawStudy,
    StudyMetadataPatchDTO,
    StudyMetadataDTO,
    StudyDownloadDTO,
    MatrixAggregationResult,
    StudySimResultDTO,
    CommentsDto,
    STUDY_REFERENCE_TEMPLATES,
    NEW_DEFAULT_STUDY_VERSION,
    PatchStudy,
    MatrixIndex,
    PatchCluster,
    PatchArea,
)
from antarest.study.repository import StudyMetadataRepository
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfigDTO,
)
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import (
    IniFileNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import INode
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import (
    InputSeriesMatrix,
)
from antarest.study.storage.rawstudy.model.filesystem.raw_file_node import (
    RawFileNode,
)
from antarest.study.storage.rawstudy.raw_study_service import (
    RawStudyService,
)
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.study_download_utils import StudyDownloader
from antarest.study.storage.utils import (
    get_default_workspace_path,
    is_managed,
    remove_from_cache,
    assert_permission,
    create_permission_from_study,
    get_start_date,
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
from antarest.study.storage.variantstudy.variant_study_service import (
    VariantStudyService,
)

logger = logging.getLogger(__name__)


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
        self.areas = AreaManager(self.storage_service)
        self.links = LinkManager(self.storage_service)
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

        self._assert_study_unarchived(study)
        return self.storage_service.get_storage(study).get(
            study, url, depth, formatted
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

        self._assert_study_unarchived(study)
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
        self, summary: bool, managed: bool, params: RequestParameters
    ) -> Dict[str, StudyMetadataDTO]:
        """
        Get information for all studies.
        Args:
            summary: indicate if just basic information should be retrieved
            managed: indicate if just managed studies should be retrieved
            params: request parameters

        Returns: List of study information

        """
        logger.info("Fetching study listing")
        studies: Dict[str, StudyMetadataDTO] = {}
        cache_keys = {
            (True, True): CacheConstants.STUDY_LISTING_SUMMARY_MANAGED.value,
            (True, False): CacheConstants.STUDY_LISTING_SUMMARY.value,
            (False, True): CacheConstants.STUDY_LISTING_MANAGED.value,
            (False, False): CacheConstants.STUDY_LISTING.value,
        }
        cache_key = cache_keys[(summary, managed)]
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
                    study_metadata = self._try_get_studies_information(
                        study, summary
                    )
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
                ),
                studies.values(),
            )
        }

    def _try_get_studies_information(
        self, study: Study, summary: bool
    ) -> Optional[StudyMetadataDTO]:
        try:
            return self.storage_service.get_storage(
                study
            ).get_study_information(study, summary)
        except Exception as e:
            logger.warning(
                "Failed to build study %s metadata", study.id, exc_info=e
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
        return self.storage_service.get_storage(study).get_study_information(
            study
        )

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

        if metadata_patch.name:
            study.name = metadata_patch.name
            self.repository.save(study)
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

        new_metadata = self.storage_service.get_storage(
            study
        ).patch_update_study_metadata(study, metadata_patch)
        self.event_bus.push(
            Event(
                type=EventType.STUDY_EDITED,
                payload=study.to_json_summary(),
                permissions=create_permission_from_study(study),
            )
        )
        return new_metadata

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
        return self.storage_service.get_storage(study).get_synthesis(
            study, params
        )

    def get_input_matrix_startdate(
        self, study_id: str, params: RequestParameters
    ) -> MatrixIndex:
        study = self.get_study(study_id)
        assert_permission(params.user, study, StudyPermissionType.READ)
        return get_start_date(
            self.storage_service.get_storage(study).get_raw(study)
        )

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

    def sync_studies_on_disk(self, folders: List[StudyFolder]) -> None:
        """
        Used by watcher to send list of studies present on filesystem.

        Args:
            folders: list of studies currently present on folder

        Returns:

        """
        # delete orphan studies on database
        paths = [str(f.path) for f in folders]
        for study in self.repository.get_all():
            if (
                isinstance(study, RawStudy)
                and not study.archived
                and (
                    study.workspace != DEFAULT_WORKSPACE_NAME
                    and study.path not in paths
                )
            ):
                logger.info(
                    "Study=%s is not present in disk and will be deleted",
                    study.id,
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
        paths = [
            study.path
            for study in self.repository.get_all()
            if isinstance(study, RawStudy)
        ]
        for folder in folders:
            if str(folder.path) not in paths:
                try:
                    base_path = self.config.storage.workspaces[
                        folder.workspace
                    ].path
                    dir_name = folder.path.relative_to(base_path)
                    study = RawStudy(
                        id=str(uuid4()),
                        name=folder.path.name,
                        path=str(folder.path),
                        folder=str(dir_name),
                        workspace=folder.workspace,
                        owner=None,
                        groups=folder.groups,
                        public_mode=PublicMode.FULL
                        if len(folder.groups) == 0
                        else PublicMode.NONE,
                    )

                    self.storage_service.raw_study_service.update_from_raw_meta(
                        study, fallback_on_default=True
                    )

                    logger.warning("Skipping study format error analysis")
                    # TODO re enable this on an async worker
                    # study.content_status = self._analyse_study(study)

                    logger.info(
                        "Study=%s appears on disk and will be added", study.id
                    )
                    self.event_bus.push(
                        Event(
                            type=EventType.STUDY_CREATED,
                            payload=study.to_json_summary(),
                            permissions=create_permission_from_study(study),
                        )
                    )
                    self.repository.save(study)
                except Exception as e:
                    logger.error(
                        f"Failed to add study {folder.path}", exc_info=e
                    )

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
        outputs: bool = True,
    ) -> None:
        logger.info(f"Flat exporting study {uuid}")
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.READ)
        self._assert_study_unarchived(study)

        return self.storage_service.get_storage(study).export_study_flat(
            study, dest, outputs
        )

    def delete_study(self, uuid: str, params: RequestParameters) -> None:
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
                type=EventType.STUDY_EDITED,
                payload=study.to_json_summary(),
                permissions=create_permission_from_study(study),
            )
        )

        logger.info(
            "delete output %s on study %s by user %s",
            output_name,
            uuid,
            params.get_user_id(),
        )

    def download_outputs(
        self,
        study_id: str,
        output_id: str,
        data: StudyDownloadDTO,
        params: RequestParameters,
    ) -> MatrixAggregationResult:
        """
        Download outputs
        Args:
            study_id: study Id
            output_id: output id
            data: Json parameters
            params: request parameters

        Returns: CSV content file

        """
        # GET STUDY ID
        study = self.get_study(study_id)
        assert_permission(params.user, study, StudyPermissionType.READ)
        self._assert_study_unarchived(study)
        logger.info(
            "study %s output download ask by %s",
            study_id,
            params.get_user_id(),
        )

        matrix = StudyDownloader.build(
            self.storage_service.get_storage(study).get_raw(study),
            output_id,
            data,
        )
        return matrix

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
        self._assert_study_unarchived(study)
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
        )
        study = self.storage_service.raw_study_service.import_study(
            study, stream
        )
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
        additional_logs: Optional[List[Path]] = None,
    ) -> Optional[str]:
        """
        Import specific output simulation inside study
        Args:
            uuid: study uuid
            output: zip file with simulation folder or simulation folder path
            params: request parameters
            additional_logs: path to the simulation log

        Returns: output simulation json formatted

        """
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.RUN)
        self._assert_study_unarchived(study)

        res = self.storage_service.get_storage(study).import_output(
            study, output
        )
        if res is not None and additional_logs:
            for log_path in additional_logs:
                shutil.copyfile(
                    log_path, Path(study.path) / "output" / res / log_path.name
                )
        remove_from_cache(cache=self.cache_service, root_id=study.id)
        logger.info(
            "output added to study %s by user %s", uuid, params.get_user_id()
        )
        return res

    def _create_edit_study_command(
        self,
        tree_node: INode[
            JSON, Union[str, int, bool, float, bytes, JSON], JSON
        ],
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
            remove_from_cache(
                self.storage_service.variant_study_service.cache, study.id
            )

        elif isinstance(study_service, VariantStudyService):
            study_service.append_command(
                study_id=file_study.config.study_id,
                command=command.to_dto(),
                params=RequestParameters(user=DEFAULT_ADMIN_USER),
            )
        else:
            raise NotImplementedError()
        return command  # for testing purpose

    def edit_study(
        self,
        uuid: str,
        url: str,
        new: Union[str, bytes, JSON],
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

        self._edit_study_using_command(study=study, url=url, data=new)

        self.event_bus.push(
            Event(
                type=EventType.STUDY_EDITED,
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
        params: RequestParameters,
    ) -> List[AreaInfoDTO]:
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.READ)
        self._assert_study_unarchived(study)
        return self.areas.get_all_areas(study, area_type)

    def get_all_links(
        self,
        uuid: str,
        params: RequestParameters,
    ) -> List[LinkInfoDTO]:
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.READ)
        self._assert_study_unarchived(study)
        return self.links.get_all_links(study)

    def create_area(
        self,
        uuid: str,
        area_creation_dto: AreaCreationDTO,
        params: RequestParameters,
    ) -> AreaInfoDTO:
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.WRITE)
        self._assert_study_unarchived(study)
        return self.areas.create_area(study, area_creation_dto)

    def create_link(
        self,
        uuid: str,
        link_creation_dto: LinkInfoDTO,
        params: RequestParameters,
    ) -> LinkInfoDTO:
        study = self.get_study(uuid)
        assert_permission(params.user, study, StudyPermissionType.WRITE)
        self._assert_study_unarchived(study)
        return self.links.create_link(study, link_creation_dto)

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
        return self.areas.update_area_metadata(study, area_id, area_patch_dto)

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
        return self.areas.delete_area(study, area_id)

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
        return self.links.delete_link(study, area_from, area_to)

    def archive(self, uuid: str, params: RequestParameters) -> str:
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
                type=[TaskType.ARCHIVE],
                status=[TaskStatus.RUNNING, TaskStatus.PENDING],
            ),
            RequestParameters(user=DEFAULT_ADMIN_USER),
        ):
            raise HTTPException(
                HTTPStatus.BAD_REQUEST, "Study is already archiving"
            )

        def archive_task(notifier: TaskUpdateNotifier) -> TaskResult:
            study_to_archive = self.get_study(uuid)
            self.storage_service.raw_study_service.archive(study_to_archive)
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
                type=[TaskType.UNARCHIVE],
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
            with open(
                self.storage_service.raw_study_service.get_archive_path(
                    study_to_archive
                ),
                "rb",
            ) as fh:
                self.storage_service.raw_study_service.import_study(
                    study_to_archive, io.BytesIO(fh.read())
                )
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
        Creeate new study with owner, group or content_status.
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
                if group is None or not group.role.is_higher_or_equals(
                    RoleType.WRITER
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
