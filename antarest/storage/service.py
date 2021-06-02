import logging
from copy import deepcopy
from datetime import datetime
from io import BytesIO
from pathlib import Path
from time import time
from typing import List, IO, Optional, cast

import werkzeug
from uuid import uuid4

from antarest.common.custom_types import JSON
from antarest.common.interfaces.eventbus import IEventBus, Event, EventType
from antarest.common.jwt import JWTUser, JWTGroup
from antarest.common.roles import RoleType
from antarest.login.model import User, Group
from antarest.login.service import LoginService
from antarest.storage.business.exporter_service import ExporterService
from antarest.storage.business.importer_service import ImporterService
from antarest.common.requests import (
    RequestParameters,
    UserHasNotPermissionError,
)
from antarest.storage.business.permissions import (
    StudyPermissionType,
    check_permission,
)
from antarest.storage.business.storage_service_utils import StorageServiceUtils
from antarest.storage.business.raw_study_service import RawStudyService
from antarest.storage.model import (
    Study,
    StudyContentStatus,
    StudyFolder,
    DEFAULT_WORKSPACE_NAME,
    RawStudy,
    PublicMode,
)
from antarest.storage.repository.study import StudyMetadataRepository
from antarest.storage.web.exceptions import (
    StudyNotFoundError,
    StudyTypeUnsupported,
)


class StorageService:
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
        self.study_service = study_service
        self.importer_service = importer_service
        self.exporter_service = exporter_service
        self.user_service = user_service
        self.repository = repository
        self.event_bus = event_bus
        self.logger = logging.getLogger(self.__class__.__name__)

    def get(self, route: str, depth: int, params: RequestParameters) -> JSON:
        """
        Get study data inside filesystem
        Args:
            route: route to follow inside study structure
            depth: depth to expand tree when route matched
            params: request parameters

        Returns: data study formatted in json

        """
        uuid, url = StorageServiceUtils.extract_info_from_url(route)
        study = self._get_study(uuid)
        self._assert_permission(params.user, study, StudyPermissionType.READ)

        if isinstance(study, RawStudy):
            self.logger.info(
                "study %s data asked by user %s", uuid, params.get_user_id()
            )
            return self.study_service.get(study, url, depth)

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
        self.logger.info(
            "studies metadata asked by user %s", params.get_user_id()
        )
        return {
            study.id: self.study_service.get_study_information(study)
            for study in self._get_study_metadatas(params)
        }

    def get_study_information(
        self, uuid: str, params: RequestParameters
    ) -> JSON:
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

        self.logger.info(
            "study %s metadata asked by user %s", uuid, params.get_user_id()
        )
        return self.study_service.get_study_information(study)

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

        self.logger.info(
            "study %s path asked by user %s", uuid, params.get_user_id()
        )
        return self.study_service.get_study_path(study)

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
        study_path = str(self.study_service.get_default_workspace_path() / sid)

        raw = RawStudy(
            id=sid,
            name=study_name,
            workspace=DEFAULT_WORKSPACE_NAME,
            path=study_path,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        raw = self.study_service.create_study(raw)
        self._save_study(raw, params.user, group_ids)
        self.event_bus.push(
            Event(EventType.STUDY_CREATED, raw.to_json_summary())
        )

        self.logger.info(
            "study %d created by user %s", raw.id, params.get_user_id()
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
                self.logger.info(
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

                study.content_status = self._analyse_study(study)

                self.logger.info(
                    "Study=%s appears on disk and will be added", study.id
                )
                self.event_bus.push(
                    Event(EventType.STUDY_CREATED, study.to_json_summary())
                )
                self.repository.save(study)

    def copy_study(
        self,
        src_uuid: str,
        dest_study_name: str,
        group_ids: List[str],
        params: RequestParameters,
    ) -> str:
        """
        Copy study to an other location.

        Args:
            src_uuid: source study
            dest_study_name: destination study
            group_ids: group to attach on new study
            params: request parameters

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
                self.study_service.get_default_workspace_path() / dest_id
            ),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        study = self.study_service.copy_study(src_study, dest_study)
        self._save_study(study, params.user, group_ids)
        self.event_bus.push(
            Event(EventType.STUDY_CREATED, study.to_json_summary())
        )

        self.logger.info(
            "study %s copied to %s by user %s",
            src_study,
            study.id,
            params.get_user_id(),
        )
        return str(study.id)

    def export_study(
        self,
        uuid: str,
        params: RequestParameters,
        outputs: bool = True,
    ) -> BytesIO:
        """
        Export study to a zip file.
        Args:
            uuid: study id
            params: request parmeters
            outputs: integrate output folder in zip file

        Returns: zip file

        """
        study = self._get_study(uuid)
        self._assert_permission(params.user, study, StudyPermissionType.READ)
        if not isinstance(study, RawStudy):
            raise StudyTypeUnsupported(uuid, study.type)

        self.logger.info(
            "study %s exported by user %s", uuid, params.get_user_id()
        )
        return self.exporter_service.export_study(study, outputs)

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

        self.study_service.delete_study(study)
        self.repository.delete(study.id)
        self.event_bus.push(
            Event(EventType.STUDY_DELETED, study.to_json_summary())
        )

        self.logger.info(
            "study %s deleted by user %s", uuid, params.get_user_id()
        )

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

        self.study_service.delete_output(study, output_name)
        self.event_bus.push(
            Event(EventType.STUDY_EDITED, study.to_json_summary())
        )

        self.logger.info(
            "delete output %s on study %s by user %s",
            output_name,
            uuid,
            params.get_user_id(),
        )

    def get_matrix(self, route: str, params: RequestParameters) -> bytes:
        """
        Download matrix
        Args:
            route: matrix path
            params: request parameters

        Returns: raw content file

        """
        uuid, path = StorageServiceUtils.extract_info_from_url(route)
        study = self._get_study(uuid)
        self._assert_permission(params.user, study, StudyPermissionType.READ)
        if not isinstance(study, RawStudy):
            raise StudyTypeUnsupported(uuid, study.type)

        self.logger.info(
            "matrix %S asked by user %s", route, params.get_user_id()
        )
        return self.exporter_service.get_matrix(study, path)

    def upload_matrix(
        self, path: str, data: bytes, params: RequestParameters
    ) -> None:
        """
        Upload matrix
        Args:
            path: matrix path
            data: raw file content
            params: request parameters

        Returns:

        """
        uuid, matrix_path = StorageServiceUtils.extract_info_from_url(path)
        study = self._get_study(uuid)
        self._assert_permission(params.user, study, StudyPermissionType.WRITE)
        if not isinstance(study, RawStudy):
            raise StudyTypeUnsupported(uuid, study.type)

        self.importer_service.upload_matrix(study, matrix_path, data)

        self.event_bus.push(
            Event(EventType.STUDY_EDITED, study.to_json_summary())
        )

        self.logger.info(
            "matrix %s updated by user %s", path, params.get_user_id()
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
        path = str(self.study_service.get_default_workspace_path() / sid)
        study = RawStudy(
            id=sid,
            workspace=DEFAULT_WORKSPACE_NAME,
            path=path,
            created_at=datetime.now(),
            updated_at=datetime.now(),
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

        self.logger.info(
            "study %s imported by user %s", study.id, params.get_user_id()
        )
        return str(study.id)

    def import_output(
        self, uuid: str, stream: IO[bytes], params: RequestParameters
    ) -> JSON:
        """
        Import specific output simulation inside study
        Args:
            uuid: study uuid
            stream: zip file with simulation folder
            params: request parameters

        Returns: output simulation json formatted

        """
        study = self._get_study(uuid)
        self._assert_permission(params.user, study, StudyPermissionType.RUN)
        if not isinstance(study, RawStudy):
            raise StudyTypeUnsupported(uuid, study.type)

        res = self.importer_service.import_output(study, stream)
        self.logger.info(
            "output added to study %s by user %s", uuid, params.get_user_id()
        )
        return res

    def edit_study(
        self, route: str, new: JSON, params: RequestParameters
    ) -> JSON:
        """
        Replace data inside study.

        Args:
            route: path data target in study
            new: new data to replace
            params: request parameters

        Returns: new data replaced

        """
        uuid, url = StorageServiceUtils.extract_info_from_url(route)
        study = self._get_study(uuid)
        self._assert_permission(params.user, study, StudyPermissionType.WRITE)
        if not isinstance(study, RawStudy):
            raise StudyTypeUnsupported(uuid, study.type)

        updated = self.study_service.edit_study(study, url, new)

        self.study_service.edit_study(
            study, url="study/antares/lastsave", new=int(time())
        )

        self.event_bus.push(
            Event(EventType.STUDY_EDITED, study.to_json_summary())
        )
        self.logger.info(
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
            self.study_service.edit_study(
                study, url="study/antares/author", new=new_owner.name
            )

        self.logger.info(
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
        study.groups = (
            study.groups + group if group not in study.groups else study.groups
        )
        self.repository.save(study)

        self.logger.info(
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

        self.logger.info(
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

        self.logger.info(
            "updated public mode of study %s by user %s",
            study_id,
            params.get_user_id(),
        )

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
            sanitized = StorageServiceUtils.sanitize(uuid)
            self.logger.warning(
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
            self.logger.error("FAIL permission: user is not logged")
            raise UserHasNotPermissionError()

        if not study:
            self.logger.error("FAIL permission: study not exist")
            raise ValueError("Metadata is None")

        ok = check_permission(user, study, permission_type)
        if raising and not ok:
            self.logger.error(
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
            if self.study_service.check_errors(metadata):
                return StudyContentStatus.WARNING
            else:
                return StudyContentStatus.VALID
        except Exception as e:
            self.logger.error(e)
            return StudyContentStatus.ERROR
