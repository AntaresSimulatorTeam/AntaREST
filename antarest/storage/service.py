from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import List, IO

from antarest.common.custom_types import JSON
from antarest.login.model import User
from antarest.storage.business.exporter_service import ExporterService
from antarest.storage.business.importer_service import ImporterService
from antarest.storage.business.storage_service_parameters import (
    StorageServiceParameters,
)
from antarest.storage.business.study_service import StudyService
from antarest.storage.model import Metadata
from antarest.storage.repository.metadata import StudyMetadataRepository
from antarest.storage.web.exceptions import StudyNotFoundError


class UserHasNotPermissionError(Exception):
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

    def assert_study_exist(self, uuid: str) -> None:
        self.study_service.check_study_exist(uuid)

    def assert_study_not_exist(self, uuid: str) -> None:
        self.study_service.assert_study_not_exist(uuid)

    def is_study_existing(self, uuid: str) -> bool:
        return self.study_service.is_study_existing(uuid)

    def get_study_uuids(self) -> List[str]:
        return self.study_service.get_study_uuids()

    def get_studies_information(self) -> JSON:
        return self.study_service.get_studies_information()

    def get_study_information(self, uuid: str) -> JSON:
        return self.study_service.get_study_information(uuid)

    def get_study_path(self, uuid: str) -> Path:
        return self.study_service.get_study_path(uuid)

    def create_study(self, study_name: str) -> str:
        return self.study_service.create_study(study_name)

    def copy_study(self, src_uuid: str, dest_study_name: str) -> str:
        return self.study_service.copy_study(src_uuid, dest_study_name)

    def export_study(
        self, name: str, compact: bool = False, outputs: bool = True
    ) -> BytesIO:
        return self.exporter_service.export_study(name, compact, outputs)

    def delete_study(self, name: str) -> None:
        self.study_service.delete_study(name)

    def delete_output(self, uuid: str, output_name: str) -> None:
        self.study_service.delete_output(uuid, output_name)

    def upload_matrix(self, path: str, data: bytes) -> None:
        self.importer_service.upload_matrix(path, data)

    def import_study(
        self, stream: IO[bytes], params: StorageServiceParameters
    ) -> str:
        uuid = self.importer_service.import_study(stream)
        info = self.study_service.get_study_information(uuid)["antares"]
        meta = Metadata(
            id=uuid,
            name=info["caption"],
            version=info["version"],
            author=info["author"],
            created_at=datetime.fromtimestamp(info["created"]),
            updated_at=datetime.fromtimestamp(info["lastsave"]),
            users=[params.user],
        )

        self.repository.save(meta)
        return uuid

    def import_output(self, uuid: str, stream: IO[bytes]) -> JSON:
        return self.importer_service.import_output(uuid, stream)

    def edit_study(self, route: str, new: JSON) -> JSON:
        return self.study_service.edit_study(route, new)

    def _check_user_permission(self, user: User, uuid: str) -> None:
        md = self.repository.get(uuid)
        if not md:
            raise StudyNotFoundError(uuid)
        if user not in md.users:
            raise UserHasNotPermissionError()
