import logging
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import List, IO, Optional

import werkzeug

from antarest.common.custom_types import JSON
from antarest.login.model import User, Role
from antarest.storage.business.exporter_service import ExporterService
from antarest.storage.business.importer_service import ImporterService
from antarest.storage.business.storage_service_parameters import (
    StorageServiceParameters,
)
from antarest.storage.business.study_service import StudyService
from antarest.storage.model import Metadata
from antarest.storage.repository.metadata import StudyMetadataRepository
from antarest.storage.web.exceptions import StudyNotFoundError


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

    def get(self, route: str, params: StorageServiceParameters) -> JSON:
        uuid, _, _ = self.study_service.extract_info_from_url(route)
        self._check_user_permission(params.user, uuid)

        return self.study_service.get(route, params)

    def _get_study_uuids(self, params: StorageServiceParameters) -> List[str]:
        uuids = self.study_service.get_study_uuids()
        return [
            uuid
            for uuid in uuids
            if self._check_user_permission(params.user, uuid, raising=False)
        ]

    def get_studies_information(
        self, params: StorageServiceParameters
    ) -> JSON:
        uuids = self._get_study_uuids(params)
        return {
            uuid: self.study_service.get_study_information(uuid)
            for uuid in uuids
        }

    def get_study_information(
        self, uuid: str, params: StorageServiceParameters
    ) -> JSON:
        self._check_user_permission(params.user, uuid)
        return self.study_service.get_study_information(uuid)

    def get_study_path(
        self, uuid: str, params: StorageServiceParameters
    ) -> Path:
        self._check_user_permission(params.user, uuid)
        return self.study_service.get_study_path(uuid)

    def create_study(
        self, study_name: str, params: StorageServiceParameters
    ) -> str:
        uuid = self.study_service.create_study(study_name)
        self._save_metadata(uuid, params.user)
        return uuid

    def copy_study(
        self,
        src_uuid: str,
        dest_study_name: str,
        params: StorageServiceParameters,
    ) -> str:
        self._check_user_permission(params.user, src_uuid)
        uuid = self.study_service.copy_study(src_uuid, dest_study_name)
        self._save_metadata(uuid, params.user)

        return uuid

    def export_study(
        self,
        uuid: str,
        params: StorageServiceParameters,
        compact: bool = False,
        outputs: bool = True,
    ) -> BytesIO:
        self._check_user_permission(params.user, uuid)
        return self.exporter_service.export_study(uuid, compact, outputs)

    def delete_study(
        self, uuid: str, params: StorageServiceParameters
    ) -> None:
        self._check_user_permission(params.user, uuid)
        self.study_service.delete_study(uuid)

    def delete_output(
        self, uuid: str, output_name: str, params: StorageServiceParameters
    ) -> None:
        self._check_user_permission(params.user, uuid)
        self.study_service.delete_output(uuid, output_name)

    def upload_matrix(
        self, path: str, data: bytes, params: StorageServiceParameters
    ) -> None:
        uuid, _, _ = self.study_service.extract_info_from_url(path)
        self._check_user_permission(params.user, uuid)
        self.importer_service.upload_matrix(path, data)

    def import_study(
        self, stream: IO[bytes], params: StorageServiceParameters
    ) -> str:
        uuid = self.importer_service.import_study(stream)
        self._save_metadata(uuid, params.user)
        return uuid

    def import_output(
        self, uuid: str, stream: IO[bytes], params: StorageServiceParameters
    ) -> JSON:
        self._check_user_permission(params.user, uuid)
        res = self.importer_service.import_output(uuid, stream)
        return res

    def edit_study(
        self, route: str, new: JSON, params: StorageServiceParameters
    ) -> JSON:
        uuid, _, _ = self.study_service.extract_info_from_url(route)
        self._check_user_permission(params.user, uuid)
        return self.study_service.edit_study(route, new)

    def _save_metadata(self, uuid: str, user: Optional[User]) -> None:
        if not user:
            raise UserHasNotPermissionError

        info = self.study_service.get_study_information(uuid)["antares"]
        meta = Metadata(
            id=uuid,
            name=info["caption"],
            version=info["version"],
            author=info["author"],
            created_at=datetime.fromtimestamp(info["created"]),
            updated_at=datetime.fromtimestamp(info["lastsave"]),
            users=[user],
        )
        self.repository.save(meta)

    def _check_user_permission(
        self, user: Optional[User], uuid: str, raising: bool = True
    ) -> bool:
        def check(user: Optional[User], uuid: str) -> None:
            if not user:
                raise UserHasNotPermissionError()

            if user.role == Role.ADMIN:
                return

            md = self.repository.get(uuid)
            if not md:
                logging.warning(f"Study {uuid} not found in metadata db")
                # TODO don't raise error. Study can be added manually by user
                raise StudyNotFoundError(uuid)

            if user not in md.users:
                raise UserHasNotPermissionError()

        try:
            check(user, uuid)
            return True
        except Exception as e:
            if raising:
                raise e
            return False
