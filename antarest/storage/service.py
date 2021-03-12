import logging
from copy import deepcopy
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import List, IO, Optional

import werkzeug
from uuid import uuid4

from antarest.common.custom_types import JSON
from antarest.login.model import User, Role, Group
from antarest.storage.business.exporter_service import ExporterService
from antarest.storage.business.importer_service import ImporterService
from antarest.common.requests import (
    RequestParameters,
)
from antarest.storage.business.study_service import StudyService
from antarest.storage.model import Metadata, StudyContentStatus
from antarest.storage.repository.metadata import StudyMetadataRepository

logger = logging.getLogger(__name__)


class UserHasNotPermissionError(werkzeug.exceptions.Forbidden):
    pass


class StorageService:
    def __init__(
        self,
        study_service: StudyService,
        importer_service: ImporterService,
        exporter_service: ExporterService,
        repository: StudyMetadataRepository,
    ):
        self.study_service = study_service
        self.importer_service = importer_service
        self.exporter_service = exporter_service
        self.repository = repository

    def get(self, route: str, depth: int, params: RequestParameters) -> JSON:
        uuid, _ = self.study_service.extract_info_from_url(route)
        md = self._check_user_permission(params.user, uuid)

        return self.study_service.get(md, route, depth)

    def _get_study_metadatas(
        self, params: RequestParameters
    ) -> List[Metadata]:
        metadatas: List[Metadata] = list()

        for uuid in self.study_service.get_study_uuids():
            md = self._check_user_permission(params.user, uuid, raising=False)
            if md:
                metadatas.append(md)
        return metadatas

    def get_studies_information(self, params: RequestParameters) -> JSON:
        return {
            md.id: self.study_service.get_study_information(md)
            for md in self._get_study_metadatas(params)
        }

    def get_study_information(
        self, uuid: str, params: RequestParameters
    ) -> JSON:
        md = self._check_user_permission(params.user, uuid)
        return self.study_service.get_study_information(md)

    def get_study_path(self, uuid: str, params: RequestParameters) -> Path:
        md = self._check_user_permission(params.user, uuid)
        return self.study_service.get_study_path(md)

    def create_study(self, study_name: str, params: RequestParameters) -> str:
        md = Metadata(id=str(uuid4()), name=study_name, workspace="default")
        md = self.study_service.create_study(md)
        self._save_metadata(md, params.user)
        return str(md.id)

    def copy_study(
        self,
        src_uuid: str,
        dest_study_name: str,
        params: RequestParameters,
    ) -> str:
        src_md = self._check_user_permission(params.user, src_uuid)

        dest_md = deepcopy(src_md)
        dest_md.id = str(uuid4())
        dest_md.name = dest_study_name

        md = self.study_service.copy_study(src_md, dest_md)
        self._save_metadata(md, params.user)

        return str(md.id)

    def export_study(
        self,
        uuid: str,
        params: RequestParameters,
        compact: bool = False,
        outputs: bool = True,
    ) -> BytesIO:
        md = self._check_user_permission(params.user, uuid)
        return self.exporter_service.export_study(md, compact, outputs)

    def delete_study(self, uuid: str, params: RequestParameters) -> None:
        md = self._check_user_permission(params.user, uuid)
        self.study_service.delete_study(md)

    def delete_output(
        self, uuid: str, output_name: str, params: RequestParameters
    ) -> None:
        md = self._check_user_permission(params.user, uuid)
        self.study_service.delete_output(md, output_name)

    def upload_matrix(
        self, path: str, data: bytes, params: RequestParameters
    ) -> None:
        uuid, _ = self.study_service.extract_info_from_url(path)
        md = self._check_user_permission(params.user, uuid)
        self.importer_service.upload_matrix(md, path, data)

    def import_study(
        self, stream: IO[bytes], params: RequestParameters
    ) -> str:
        md = Metadata(id=str(uuid4()), workspace="default")
        md = self.importer_service.import_study(md, stream)
        status = (
            StudyContentStatus.ERROR
            if self.study_service.check_errors(md)
            else StudyContentStatus.VALID
        )
        self._save_metadata(md, owner=params.user, content_status=status)
        return str(md.id)

    def import_output(
        self, uuid: str, stream: IO[bytes], params: RequestParameters
    ) -> JSON:
        md = self._check_user_permission(params.user, uuid)
        res = self.importer_service.import_output(md, stream)
        return res

    def edit_study(
        self, route: str, new: JSON, params: RequestParameters
    ) -> JSON:
        uuid, _ = self.study_service.extract_info_from_url(route)
        md = self._check_user_permission(params.user, uuid)
        return self.study_service.edit_study(md, route, new)

    def _save_metadata(
        self,
        metadata: Metadata,
        owner: Optional[User] = None,
        content_status: StudyContentStatus = StudyContentStatus.VALID,
        group: Optional[Group] = None,
    ) -> None:
        if not owner and not group:
            raise UserHasNotPermissionError

        info = self.study_service.get_study_information(metadata)["antares"]

        metadata.name = info["caption"]
        metadata.version = info["version"]
        metadata.author = info["author"]
        metadata.created_at = datetime.fromtimestamp(info["created"])
        metadata.updated_at = datetime.fromtimestamp(info["lastsave"])
        metadata.content_status = content_status

        if owner:
            metadata.owner = owner
        if group:
            metadata.groups = [group]
        self.repository.save(metadata)

    def _check_user_permission(
        self, user: Optional[User], uuid: str, raising: bool = True
    ) -> Metadata:
        def check(user: Optional[User], uuid: str) -> Metadata:
            if not user:
                raise UserHasNotPermissionError()

            md = self.repository.get(uuid)
            if not md:
                logger.warning(f"Study {uuid} not found in metadata db")
                raise UserHasNotPermissionError()

            if user.role == Role.ADMIN:
                return md

            is_owner = user == md.owner

            inside_group = (
                md.groups
                and user.groups
                and any(g in md.groups for g in user.groups)
            )

            if not is_owner and not inside_group:
                raise UserHasNotPermissionError()

            return md

        try:
            return check(user, uuid)
        except Exception as e:
            if raising:
                raise e
            return None  # type: ignore
