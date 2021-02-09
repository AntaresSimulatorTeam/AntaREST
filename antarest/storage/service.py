from io import BytesIO
from pathlib import Path
from typing import List, IO

from antarest.common.custom_types import JSON
from antarest.storage.web import RequestHandler
from antarest.storage.web.request_handler import RequestHandlerParameters


class StorageService:
    def __init__(self, request_handler: RequestHandler):
        self.request_handler = request_handler

    def get(self, route: str, parameters: RequestHandlerParameters) -> JSON:
        return self.request_handler.get(route, parameters)

    def assert_study_exist(self, uuid: str) -> None:
        self.request_handler.assert_study_exist(uuid)

    def assert_study_not_exist(self, uuid: str) -> None:
        self.request_handler.assert_study_not_exist(uuid)

    def is_study_existing(self, uuid: str) -> bool:
        return self.request_handler.is_study_existing(uuid)

    def get_study_uuids(self) -> List[str]:
        return self.request_handler.get_study_uuids()

    def get_studies_informations(self) -> JSON:
        return self.request_handler.get_studies_informations()

    def get_study_informations(self, uuid: str) -> JSON:
        return self.request_handler.get_study_informations(uuid)

    def get_study_path(self, uuid: str) -> Path:
        return self.request_handler.get_study_path(uuid)

    def create_study(self, study_name: str) -> str:
        return self.request_handler.create_study(study_name)

    def copy_study(self, src_uuid: str, dest_study_name: str) -> str:
        return self.request_handler.copy_study(src_uuid, dest_study_name)

    def export_study(
        self, name: str, compact: bool = False, outputs: bool = True
    ) -> BytesIO:
        return self.request_handler.export_study(name, compact, outputs)

    def delete_study(self, name: str) -> None:
        self.request_handler.delete_study(name)

    def delete_output(self, uuid: str, output_name: str) -> None:
        self.request_handler.delete_output(uuid, output_name)

    def upload_matrix(self, path: str, data: bytes) -> None:
        self.request_handler.upload_matrix(path, data)

    def import_study(self, stream: IO[bytes]) -> str:
        return self.request_handler.import_study(stream)

    def import_output(self, uuid: str, stream: IO[bytes]) -> JSON:
        return self.request_handler.import_output(uuid, stream)

    def edit_study(self, route: str, new: JSON) -> JSON:
        return self.request_handler.edit_study(route, new)
