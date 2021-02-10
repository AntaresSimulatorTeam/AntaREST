from io import BytesIO
from pathlib import Path
from typing import IO, List

from antarest.common.custom_types import JSON
from antarest.storage.service import StorageService, StorageServiceParameters


class RequestHandler:
    def __init__(self, storage_service: StorageService):
        self.storage_service = storage_service

    def get(self, route: str, parameters: StorageServiceParameters) -> JSON:
        return self.storage_service.get(route, parameters)

    def assert_study_exist(self, uuid: str) -> None:
        self.storage_service.assert_study_exist(uuid)

    def assert_study_not_exist(self, uuid: str) -> None:
        self.storage_service.assert_study_not_exist(uuid)

    def is_study_existing(self, uuid: str) -> bool:
        return self.storage_service.is_study_existing(uuid)

    def get_study_uuids(self) -> List[str]:
        return self.storage_service.get_study_uuids()

    def get_studies_information(self) -> JSON:
        return self.storage_service.get_studies_information()

    def get_study_information(self, uuid: str) -> JSON:
        return self.storage_service.get_study_information(uuid)

    def get_study_path(self, uuid: str) -> Path:
        return self.storage_service.get_study_path(uuid)

    def create_study(self, study_name: str) -> str:
        return self.storage_service.create_study(study_name)

    def copy_study(self, src_uuid: str, dest_study_name: str) -> str:
        return self.storage_service.copy_study(src_uuid, dest_study_name)

    def export_study(
        self, name: str, compact: bool = False, outputs: bool = True
    ) -> BytesIO:
        return self.storage_service.export_study(name, compact, outputs)

    def delete_study(self, name: str) -> None:
        self.storage_service.delete_study(name)

    def delete_output(self, uuid: str, output_name: str) -> None:
        self.storage_service.delete_output(uuid, output_name)

    def upload_matrix(self, path: str, data: bytes) -> None:
        self.storage_service.upload_matrix(path, data)

    def import_study(self, stream: IO[bytes]) -> str:
        return self.storage_service.import_study(stream)

    def import_output(self, uuid: str, stream: IO[bytes]) -> JSON:
        return self.storage_service.import_output(uuid, stream)

    def edit_study(self, route: str, new: JSON) -> JSON:
        return self.storage_service.edit_study(route, new)
