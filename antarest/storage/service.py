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
from antarest.storage.business.raw_study_service import StudyService
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

logger = logging.getLogger(__name__)


class StorageService:
    def __init__(
        self,
        study_service: StudyService,
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

    def get(self, route: str, depth: int, params: RequestParameters) -> JSON:
        uuid, url = StorageServiceUtils.extract_info_from_url(route)
        study = self._get_study(uuid)
        self._assert_permission(params.user, study, StudyPermissionType.READ)

        if isinstance(study, RawStudy):
            return self.study_service.get(study, url, depth)

        raise StudyTypeUnsupported(
            f"Study {uuid} with type {study.type} not recognized"
        )

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
        return {
            study.id: self.study_service.get_study_information(study)
            for study in self._get_study_metadatas(params)
        }

    def get_study_information(
        self, uuid: str, params: RequestParameters
    ) -> JSON:
        study = self._get_study(uuid)
        self._assert_permission(params.user, study, StudyPermissionType.READ)
        if not isinstance(study, RawStudy):
            raise StudyTypeUnsupported(
                f"Study {uuid} with type {study.type} not recognized"
            )

        return self.study_service.get_study_information(study)

    def get_study_path(self, uuid: str, params: RequestParameters) -> Path:
        study = self._get_study(uuid)
        self._assert_permission(params.user, study, StudyPermissionType.RUN)

        if not isinstance(study, RawStudy):
            raise StudyTypeUnsupported(
                f"Study {uuid} with type {study.type} not recognized"
            )

        return self.study_service.get_study_path(study)

    def create_study(
        self, study_name: str, group_ids: List[str], params: RequestParameters
    ) -> str:
        sid = str(uuid4())
        study_path = str(self.study_service.get_default_workspace_path() / sid)
        raw = RawStudy(
            id=sid,
            name=study_name,
            workspace=DEFAULT_WORKSPACE_NAME,
            path=study_path,
        )
        raw = self.study_service.create_study(raw)
        self._save_study(raw, params.user, group_ids)
        self.event_bus.push(
            Event(EventType.STUDY_CREATED, raw.to_json_summary())
        )
        return str(raw.id)

    def sync_studies_on_disk(self, folders: List[StudyFolder]) -> None:

        # delete orphan studies on database
        paths = [str(f.path) for f in folders]
        for study in self.repository.get_all():
            if isinstance(study, RawStudy) and (
                study.workspace != DEFAULT_WORKSPACE_NAME
                and study.path not in paths
            ):
                logger.info(
                    f"Study={study.id} is not present in disk and will be deleted"
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

                logger.info(
                    f"Study={study.id} appears on disk and will be added"
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
        src_study = self._get_study(src_uuid)
        self._assert_permission(
            params.user, src_study, StudyPermissionType.READ
        )

        if not isinstance(src_study, RawStudy):
            raise StudyTypeUnsupported(
                f"Study {src_uuid} with type {src_study.type} not recognized"
            )

        dest_study = deepcopy(src_study)
        dest_study.id = str(uuid4())
        dest_study.name = dest_study_name
        dest_study.workspace = DEFAULT_WORKSPACE_NAME
        dest_study.path = str(
            self.study_service.get_default_workspace_path() / dest_study.id
        )

        study = self.study_service.copy_study(src_study, dest_study)
        self._save_study(study, params.user, group_ids)
        self.event_bus.push(
            Event(EventType.STUDY_CREATED, study.to_json_summary())
        )
        return str(study.id)

    def export_study(
        self,
        uuid: str,
        params: RequestParameters,
        outputs: bool = True,
    ) -> BytesIO:
        study = self._get_study(uuid)
        self._assert_permission(params.user, study, StudyPermissionType.READ)
        if not isinstance(study, RawStudy):
            raise StudyTypeUnsupported(
                f"Study {uuid} with type {study.type} not recognized"
            )

        return self.exporter_service.export_study(study, outputs)

    def delete_study(self, uuid: str, params: RequestParameters) -> None:
        study = self._get_study(uuid)
        self._assert_permission(params.user, study, StudyPermissionType.DELETE)
        if not isinstance(study, RawStudy):
            raise StudyTypeUnsupported(
                f"Study {uuid} with type {study.type} not recognized"
            )

        self.study_service.delete_study(study)
        self.repository.delete(study.id)
        self.event_bus.push(
            Event(EventType.STUDY_DELETED, study.to_json_summary())
        )

    def delete_output(
        self, uuid: str, output_name: str, params: RequestParameters
    ) -> None:
        study = self._get_study(uuid)
        self._assert_permission(params.user, study, StudyPermissionType.WRITE)
        if not isinstance(study, RawStudy):
            raise StudyTypeUnsupported(
                f"Study {uuid} with type {study.type} not recognized"
            )

        self.study_service.delete_output(study, output_name)
        self.event_bus.push(
            Event(EventType.STUDY_EDITED, study.to_json_summary())
        )

    def get_matrix(self, route: str, params: RequestParameters) -> bytes:
        uuid, path = StorageServiceUtils.extract_info_from_url(route)
        study = self._get_study(uuid)
        self._assert_permission(params.user, study, StudyPermissionType.READ)
        if not isinstance(study, RawStudy):
            raise StudyTypeUnsupported(
                f"Study {uuid} with type {study.type} not recognized"
            )

        return self.exporter_service.get_matrix(study, path)

    def upload_matrix(
        self, path: str, data: bytes, params: RequestParameters
    ) -> None:
        uuid, matrix_path = StorageServiceUtils.extract_info_from_url(path)
        study = self._get_study(uuid)
        self._assert_permission(params.user, study, StudyPermissionType.WRITE)
        if not isinstance(study, RawStudy):
            raise StudyTypeUnsupported(
                f"Study {uuid} with type {study.type} not recognized"
            )

        self.importer_service.upload_matrix(study, matrix_path, data)

        self.event_bus.push(
            Event(EventType.STUDY_EDITED, study.to_json_summary())
        )

    def import_study(
        self,
        stream: IO[bytes],
        group_ids: List[str],
        params: RequestParameters,
    ) -> str:
        sid = str(uuid4())
        path = str(self.study_service.get_default_workspace_path() / sid)
        study = RawStudy(id=sid, workspace=DEFAULT_WORKSPACE_NAME, path=path)
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
        return str(study.id)

    def import_output(
        self, uuid: str, stream: IO[bytes], params: RequestParameters
    ) -> JSON:
        study = self._get_study(uuid)
        self._assert_permission(params.user, study, StudyPermissionType.RUN)
        if not isinstance(study, RawStudy):
            raise StudyTypeUnsupported(
                f"Study {uuid} with type {study.type} not recognized"
            )

        res = self.importer_service.import_output(study, stream)
        return res

    def edit_study(
        self, route: str, new: JSON, params: RequestParameters
    ) -> JSON:
        uuid, url = StorageServiceUtils.extract_info_from_url(route)
        study = self._get_study(uuid)
        self._assert_permission(params.user, study, StudyPermissionType.WRITE)
        if not isinstance(study, RawStudy):
            raise StudyTypeUnsupported(
                f"Study {uuid} with type {study.type} not recognized"
            )

        updated = self.study_service.edit_study(study, url, new)

        self.study_service.edit_study(
            study, url="study/antares/lastsave", new=int(time())
        )

        self.event_bus.push(
            Event(EventType.STUDY_EDITED, study.to_json_summary())
        )
        return cast(JSON, updated)

    def change_owner(
        self, study_id: str, owner_id: int, params: RequestParameters
    ) -> None:
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

    def add_group(
        self, study_id: str, group_id: str, params: RequestParameters
    ) -> None:
        study = self._get_study(study_id)
        self._assert_permission(
            params.user, study, StudyPermissionType.MANAGE_PERMISSIONS
        )
        group = self.user_service.get_group(group_id, params)
        study.groups = (
            study.groups + group if group not in study.groups else study.groups
        )
        self.repository.save(study)

    def remove_group(
        self, study_id: str, group_id: str, params: RequestParameters
    ) -> None:
        study = self._get_study(study_id)
        self._assert_permission(
            params.user, study, StudyPermissionType.MANAGE_PERMISSIONS
        )
        study.groups = [
            group for group in study.groups if group.id != group_id
        ]
        self.repository.save(study)

    def set_public_mode(
        self, study_id: str, mode: PublicMode, params: RequestParameters
    ) -> None:
        study = self._get_study(study_id)
        self._assert_permission(
            params.user, study, StudyPermissionType.MANAGE_PERMISSIONS
        )
        study.public_mode = mode
        self.repository.save(study)

    def _save_study(
        self,
        study: RawStudy,
        owner: Optional[JWTUser] = None,
        group_ids: List[str] = list(),
        content_status: StudyContentStatus = StudyContentStatus.VALID,
    ) -> None:
        if not owner:
            raise UserHasNotPermissionError

        info = self.study_service.get_study_information(study)["antares"]

        study.name = info["caption"]
        study.version = info["version"]
        study.author = info["author"]
        study.created_at = datetime.fromtimestamp(info["created"])
        study.updated_at = datetime.fromtimestamp(info["lastsave"])
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

        study = self.repository.get(uuid)
        if not study:
            sanitized = StorageServiceUtils.sanitize(uuid)
            logger.warning(
                f"Study %s not found in metadata db",
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
        if not user:
            raise UserHasNotPermissionError()

        if not study:
            raise ValueError("Metadata is None")

        ok = check_permission(user, study, permission_type)
        if raising and not ok:
            raise UserHasNotPermissionError()

        return ok

    def _analyse_study(self, metadata: RawStudy) -> StudyContentStatus:
        try:
            if self.study_service.check_errors(metadata):
                return StudyContentStatus.WARNING
            else:
                return StudyContentStatus.VALID
        except Exception as e:
            logger.error(e)
            return StudyContentStatus.ERROR
