import logging
from datetime import datetime
from pathlib import Path
from time import time
from typing import List, IO, Optional, cast, Union
from uuid import uuid4

from markupsafe import escape

from antarest.core.custom_types import JSON
from antarest.core.interfaces.eventbus import IEventBus, Event, EventType
from antarest.core.jwt import JWTUser
from antarest.core.requests import (
    RequestParameters,
    UserHasNotPermissionError,
)
from antarest.core.roles import RoleType
from antarest.login.model import Group
from antarest.login.service import LoginService
from antarest.study.storage.area_management import (
    AreaManager,
    AreaType,
    AreaInfoDTO,
    AreaCreationDTO,
    AreaPatchUpdateDTO,
)
from antarest.study.storage.rawstudy.exporter_service import ExporterService
from antarest.study.storage.rawstudy.importer_service import ImporterService
from antarest.study.storage.permissions import (
    StudyPermissionType,
    check_permission,
)
from antarest.study.storage.rawstudy.raw_study_service import (
    RawStudyService,
)
from antarest.study.storage.study_download_utils import StudyDownloader
from antarest.study.model import (
    Study,
    StudyContentStatus,
    StudyFolder,
    DEFAULT_WORKSPACE_NAME,
    RawStudy,
    PublicMode,
    StudyMetadataPatchDTO,
    StudyMetadataDTO,
    StudyDownloadDTO,
    MatrixAggregationResult,
    StudySimResultDTO,
)
from antarest.study.repository import StudyMetadataRepository
from antarest.core.exceptions import (
    StudyNotFoundError,
    StudyTypeUnsupported,
)

logger = logging.getLogger(__name__)


class StudyService:
    """
    Storage module facade service to handle studies management.
    """

    def __init__(
        self,
        study_service: RawStudyService,
        importer_service: ImporterService,
        exporter_service: ExporterService,
        user_service: LoginService,
        repository: StudyMetadataRepository,
        event_bus: IEventBus,
    ):
        self.raw_study_service = study_service
        self.importer_service = importer_service
        self.exporter_service = exporter_service
        self.user_service = user_service
        self.repository = repository
        self.event_bus = event_bus
        self.areas = AreaManager(self.raw_study_service)

    def get(
        self, uuid: str, url: str, depth: int, params: RequestParameters
    ) -> JSON:
        """
        Get study data inside filesystem
        Args:
            uuid: study uuid
            url: route to follow inside study structure
            depth: depth to expand tree when route matched
            params: request parameters

        Returns: data study formatted in json

        """
        study = self._get_study(uuid)
        self._assert_permission(params.user, study, StudyPermissionType.READ)

        if isinstance(study, RawStudy):
            logger.info(
                "study %s data asked by user %s", uuid, params.get_user_id()
            )
            return self.raw_study_service.get(study, url, depth)

        raise StudyTypeUnsupported(uuid, study.type)

    def _get_study_metadatas(self, params: RequestParameters) -> List[Study]:
        return list(
            filter(
                lambda study: self._assert_permission(
                    params.user, study, StudyPermissionType.READ, raising=False
                ),
                self.repository.get_all(),
            )
        )

    def get_studies_information(self, params: RequestParameters) -> JSON:
        """
        Get information for all studies.
        Args:
            params: request parameters

        Returns: List of study information

        """
        logger.info("studies metadata asked by user %s", params.get_user_id())
        return {
            study.id: self.raw_study_service.get_study_information(
                study, summary=True
            )
            for study in self._get_study_metadatas(params)
        }

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
        study = self._get_study(uuid)
        self._assert_permission(params.user, study, StudyPermissionType.READ)
        if not isinstance(study, RawStudy):
            raise StudyTypeUnsupported(uuid, study.type)

        logger.info(
            "study %s metadata asked by user %s", uuid, params.get_user_id()
        )
        return self.raw_study_service.get_study_information(study)

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
        study = self._get_study(uuid)
        self._assert_permission(params.user, study, StudyPermissionType.READ)
        if not isinstance(study, RawStudy):
            raise StudyTypeUnsupported(uuid, study.type)

        if metadata_patch.name:
            study.name = metadata_patch.name
            self.repository.save(study)
        if metadata_patch.horizon:
            study_settings_url = "settings/generaldata/general"
            study_settings = self.raw_study_service.get(
                study, study_settings_url
            )
            study_settings["horizon"] = metadata_patch.horizon
            self.raw_study_service.edit_study(
                study, study_settings_url, study_settings
            )

        return self.raw_study_service.patch_update_study_metadata(
            study, metadata_patch
        )

    def get_study_path(self, uuid: str, params: RequestParameters) -> Path:
        """
        Retrieve study path
        Args:
            uuid: study uuid
            params: request parameters

        Returns:

        """
        study = self._get_study(uuid)
        self._assert_permission(params.user, study, StudyPermissionType.RUN)

        if not isinstance(study, RawStudy):
            raise StudyTypeUnsupported(uuid, study.type)

        logger.info(
            "study %s path asked by user %s", uuid, params.get_user_id()
        )
        return self.raw_study_service.get_study_path(study)

    def create_study(
        self, study_name: str, group_ids: List[str], params: RequestParameters
    ) -> str:
        """
        Create empty study
        Args:
            study_name: study name to set
            group_ids: group to link to study
            params: request parameters

        Returns: new study uuid

        """
        sid = str(uuid4())
        study_path = str(
            self.raw_study_service.get_default_workspace_path() / sid
        )

        raw = RawStudy(
            id=sid,
            name=study_name,
            workspace=DEFAULT_WORKSPACE_NAME,
            path=study_path,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            version=RawStudyService.new_default_version,
        )

        raw = self.raw_study_service.create(raw)
        self._save_study(raw, params.user, group_ids)
        self.event_bus.push(
            Event(EventType.STUDY_CREATED, raw.to_json_summary())
        )

        logger.info(
            "study %s created by user %s", raw.id, params.get_user_id()
        )
        return str(raw.id)

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
            if isinstance(study, RawStudy) and (
                study.workspace != DEFAULT_WORKSPACE_NAME
                and study.path not in paths
            ):
                logger.info(
                    "Study=%s is not present in disk and will be deleted",
                    study.id,
                )
                self.event_bus.push(
                    Event(EventType.STUDY_DELETED, study.to_json_summary())
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
                    study = RawStudy(
                        id=str(uuid4()),
                        name=folder.path.name,
                        path=str(folder.path),
                        workspace=folder.workspace,
                        owner=None,
                        groups=folder.groups,
                        public_mode=PublicMode.FULL
                        if len(folder.groups) == 0
                        else PublicMode.NONE,
                    )

                    self.raw_study_service.update_from_raw_meta(
                        study, fallback_on_default=True
                    )

                    logger.warning("Skipping study format error analysis")
                    # TODO re enable this on an async worker
                    # study.content_status = self._analyse_study(study)

                    logger.info(
                        "Study=%s appears on disk and will be added", study.id
                    )
                    self.event_bus.push(
                        Event(EventType.STUDY_CREATED, study.to_json_summary())
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

        Returns:

        """
        src_study = self._get_study(src_uuid)
        self._assert_permission(
            params.user, src_study, StudyPermissionType.READ
        )

        if not isinstance(src_study, RawStudy):
            raise StudyTypeUnsupported(src_uuid, src_study.type)

        dest_id = str(uuid4())
        dest_study = RawStudy(
            id=dest_id,
            name=dest_study_name,
            workspace=DEFAULT_WORKSPACE_NAME,
            path=str(
                self.raw_study_service.get_default_workspace_path() / dest_id
            ),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            version=src_study.version,
        )

        study = self.raw_study_service.copy(
            src_study, dest_study, with_outputs
        )
        self._save_study(study, params.user, group_ids)
        self.event_bus.push(
            Event(EventType.STUDY_CREATED, study.to_json_summary())
        )

        logger.info(
            "study %s copied to %s by user %s",
            src_study,
            study.id,
            params.get_user_id(),
        )
        return str(study.id)

    def export_study(
        self,
        uuid: str,
        target: Path,
        params: RequestParameters,
        outputs: bool = True,
    ) -> Path:
        """
        Export study to a zip file.
        Args:
            uuid: study id
            target: export path
            params: request parmeters
            outputs: integrate output folder in zip file

        """
        study = self._get_study(uuid)
        self._assert_permission(params.user, study, StudyPermissionType.READ)
        if not isinstance(study, RawStudy):
            raise StudyTypeUnsupported(uuid, study.type)

        logger.info("study %s exported by user %s", uuid, params.get_user_id())
        return self.exporter_service.export_study(study, target, outputs)

    def export_study_flat(
        self,
        uuid: str,
        params: RequestParameters,
        dest: Path,
        outputs: bool = True,
    ) -> None:
        study = self._get_study(uuid)
        self._assert_permission(params.user, study, StudyPermissionType.READ)
        if not isinstance(study, RawStudy):
            raise StudyTypeUnsupported(uuid, study.type)

        return self.exporter_service.export_study_flat(study, dest, outputs)

    def delete_study(self, uuid: str, params: RequestParameters) -> None:
        """
        Delete study
        Args:
            uuid: study uuid
            params: request parameters

        Returns:

        """
        study = self._get_study(uuid)
        self._assert_permission(params.user, study, StudyPermissionType.DELETE)
        if not isinstance(study, RawStudy):
            raise StudyTypeUnsupported(uuid, study.type)

        self.raw_study_service.delete(study)
        self.repository.delete(study.id)
        self.event_bus.push(
            Event(EventType.STUDY_DELETED, study.to_json_summary())
        )

        logger.info("study %s deleted by user %s", uuid, params.get_user_id())

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
        study = self._get_study(uuid)
        self._assert_permission(params.user, study, StudyPermissionType.WRITE)
        if not isinstance(study, RawStudy):
            raise StudyTypeUnsupported(uuid, study.type)

        self.raw_study_service.delete_output(study, output_name)
        self.event_bus.push(
            Event(EventType.STUDY_EDITED, study.to_json_summary())
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
        study = self._get_study(study_id)
        self._assert_permission(params.user, study, StudyPermissionType.READ)

        if not isinstance(study, RawStudy):
            raise StudyTypeUnsupported(study_id, study.type)

        logger.info(
            "study %s output download ask by %s",
            study_id,
            params.get_user_id(),
        )

        matrix = StudyDownloader.build(
            self.raw_study_service.get_raw(study), output_id, data
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
        study = self._get_study(study_id)
        self._assert_permission(params.user, study, StudyPermissionType.READ)

        if not isinstance(study, RawStudy):
            raise StudyTypeUnsupported(study_id, study.type)

        logger.info(
            "study %s output listing asked by user %s",
            study_id,
            params.get_user_id(),
        )

        return self.raw_study_service.get_study_sim_result(study)

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
        study = self._get_study(study_id)
        self._assert_permission(params.user, study, StudyPermissionType.WRITE)

        if not isinstance(study, RawStudy):
            raise StudyTypeUnsupported(study_id, study.type)

        logger.info(
            "output %s set by user %s as reference (%b) for study %s",
            output_id,
            params.get_user_id(),
            status,
            study_id,
        )

        self.raw_study_service.set_reference_output(study, output_id, status)

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
        path = str(self.raw_study_service.get_default_workspace_path() / sid)
        study = RawStudy(
            id=sid,
            workspace=DEFAULT_WORKSPACE_NAME,
            path=path,
        )
        study = self.importer_service.import_study(study, stream)
        status = self._analyse_study(study)
        self._save_study(
            study,
            owner=params.user,
            group_ids=group_ids,
            content_status=status,
        )
        self.event_bus.push(
            Event(EventType.STUDY_CREATED, study.to_json_summary())
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
    ) -> Optional[str]:
        """
        Import specific output simulation inside study
        Args:
            uuid: study uuid
            output: zip file with simulation folder or simulation folder path
            params: request parameters

        Returns: output simulation json formatted

        """
        study = self._get_study(uuid)
        self._assert_permission(params.user, study, StudyPermissionType.RUN)
        if not isinstance(study, RawStudy):
            raise StudyTypeUnsupported(uuid, study.type)

        res = self.importer_service.import_output(study, output)
        logger.info(
            "output added to study %s by user %s", uuid, params.get_user_id()
        )
        return res

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
        study = self._get_study(uuid)
        self._assert_permission(params.user, study, StudyPermissionType.WRITE)
        if not isinstance(study, RawStudy):
            raise StudyTypeUnsupported(uuid, study.type)

        updated = self.raw_study_service.edit_study(study, url, new)

        self.raw_study_service.edit_study(
            study, url="study/antares/lastsave", new=int(time())
        )

        self.event_bus.push(
            Event(EventType.STUDY_EDITED, study.to_json_summary())
        )
        logger.info(
            "data %s on study %s updated by user %s",
            url,
            uuid,
            params.get_user_id(),
        )
        return cast(JSON, updated)

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
        study = self._get_study(study_id)
        self._assert_permission(
            params.user, study, StudyPermissionType.MANAGE_PERMISSIONS
        )
        new_owner = self.user_service.get_user(owner_id, params)
        study.owner = new_owner
        self.repository.save(study)

        if isinstance(study, RawStudy) and new_owner:
            self.raw_study_service.edit_study(
                study, url="study/antares/author", new=new_owner.name
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
        study = self._get_study(study_id)
        self._assert_permission(
            params.user, study, StudyPermissionType.MANAGE_PERMISSIONS
        )
        group = self.user_service.get_group(group_id, params)
        study.groups = study.groups + [
            group if group not in study.groups else study.groups
        ]
        self.repository.save(study)

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
        study = self._get_study(study_id)
        self._assert_permission(
            params.user, study, StudyPermissionType.MANAGE_PERMISSIONS
        )
        study.groups = [
            group for group in study.groups if group.id != group_id
        ]
        self.repository.save(study)

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
        study = self._get_study(study_id)
        self._assert_permission(
            params.user, study, StudyPermissionType.MANAGE_PERMISSIONS
        )
        study.public_mode = mode
        self.repository.save(study)

        logger.info(
            "updated public mode of study %s by user %s",
            study_id,
            params.get_user_id(),
        )

    def check_errors(self, uuid: str) -> List[str]:
        study = self._get_study(uuid)
        return self.raw_study_service.check_errors(cast(RawStudy, study))

    def get_all_areas(
        self,
        uuid: str,
        area_type: Optional[AreaType],
        params: RequestParameters,
    ) -> List[AreaInfoDTO]:
        study = self._get_study(uuid)
        self._assert_permission(params.user, study, StudyPermissionType.READ)
        return self.areas.get_all_areas(study, area_type)

    def create_area(
        self,
        uuid: str,
        area_creation_dto: AreaCreationDTO,
        params: RequestParameters,
    ) -> AreaInfoDTO:
        study = self._get_study(uuid)
        self._assert_permission(params.user, study, StudyPermissionType.WRITE)
        return self.areas.create_area(study, area_creation_dto)

    def update_area(
        self,
        uuid: str,
        area_id: str,
        area_patch_dto: AreaPatchUpdateDTO,
        params: RequestParameters,
    ) -> AreaInfoDTO:
        study = self._get_study(uuid)
        self._assert_permission(params.user, study, StudyPermissionType.WRITE)
        return self.areas.update_area(study, area_id, area_patch_dto)

    def delete_area(
        self, uuid: str, area_id: str, params: RequestParameters
    ) -> None:
        study = self._get_study(uuid)
        self._assert_permission(params.user, study, StudyPermissionType.WRITE)
        return self.areas.delete_area(study, area_id)

    def _save_study(
        self,
        study: RawStudy,
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

    def _get_study(self, uuid: str) -> Study:
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

    def _assert_permission(
        self,
        user: Optional[JWTUser],
        study: Optional[Study],
        permission_type: StudyPermissionType,
        raising: bool = True,
    ) -> bool:
        """
        Assert user has permission to edit or read study.
        Args:
            user: user logged
            study: study asked
            permission_type: level of permission
            raising: raise error if permission not matched

        Returns: true if permission match, false if not raising.

        """
        if not user:
            logger.error("FAIL permission: user is not logged")
            raise UserHasNotPermissionError()

        if not study:
            logger.error("FAIL permission: study not exist")
            raise ValueError("Metadata is None")

        ok = check_permission(user, study, permission_type)
        if raising and not ok:
            logger.error(
                "FAIL permission: user %d has no permission on study %s",
                user.id,
                study.id,
            )
            raise UserHasNotPermissionError()

        return ok

    def _analyse_study(self, metadata: RawStudy) -> StudyContentStatus:
        """
        Analyze study integrity
        Args:
            metadata: study to analyze

        Returns: VALID if study has any integrity mistakes.
        WARNING if studies has mistakes.
        ERROR if tree was not able to analyse structuree without raise error.

        """
        try:
            if self.raw_study_service.check_errors(metadata):
                return StudyContentStatus.WARNING
            else:
                return StudyContentStatus.VALID
        except Exception as e:
            logger.error(e)
            return StudyContentStatus.ERROR
