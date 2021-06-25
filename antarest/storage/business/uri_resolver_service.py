import re
from pathlib import Path
from typing import Union, Optional

from antarest.common.config import Config
from antarest.common.custom_types import JSON
from antarest.common.jwt import DEFAULT_ADMIN_USER
from antarest.common.requests import RequestParameters
from antarest.matrixstore.service import MatrixService
from antarest.storage.model import DEFAULT_WORKSPACE_NAME


class UriResolverService:
    def __init__(self, config: Config, matrix_service: MatrixService):
        self.config = config
        # StorageService must be injected after the class creation to avoid circular injection
        self.storage_service = None  # type: ignore
        self.matrix_service = matrix_service

    def resolve(self, uri: str) -> Union[str, JSON]:
        match = re.match(r"^(\w+)://([\w-]+)/?(.*)$", uri)
        if not match:
            raise ValueError("Pattern Uri not found")

        protocol = match.group(1)
        id = match.group(2)
        path = match.group(3)

        if protocol == "studyfile":
            return self._resolve_studyfile(id, path)
        if protocol == "matrix":
            return self._resolve_matrix(id)
        raise NotImplementedError(f"protocol {protocol} not implemented")

    def _resolve_matrix(self, id: str) -> JSON:
        data = self.matrix_service.get(id)
        if data:
            return {
                "data": data.data,
                "index": data.index,
                "columns": data.columns,
            }
        raise ValueError(f"id matrix {id} not found")

    def _get_path(self, study_id: str) -> Path:
        if self.storage_service is not None:
            return self.storage_service.get_study_path(
                study_id, RequestParameters(user=DEFAULT_ADMIN_USER)
            )
        else:
            raise NotImplementedError("Storage service is not injected")

    def _resolve_studyfile(self, id: str, path: str) -> bytes:
        file = self._get_path(id) / path
        if file.exists():
            print(file)
            return file.read_bytes()
        else:
            raise ValueError(f"File Not Found {file.absolute()}")

    def build_studyfile_uri(self, path: Path, study_id: str) -> str:
        # extract path after study id
        relative_path = str(path.absolute()).split(f"{study_id}/")[1]
        uri = f"studyfile://{study_id}/{relative_path}"
        return uri

    def build_matrix_uri(self, id) -> str:
        return f"matrix://{id}"

    def is_managed(self, study_id) -> bool:
        default = self.config.storage.workspaces[DEFAULT_WORKSPACE_NAME]
        if self.storage_service is not None:
            return (
                default
                in self.storage_service.get_study_path(
                    study_id, RequestParameters(user=DEFAULT_ADMIN_USER)
                ).parts
            )
        else:
            raise NotImplementedError("Storage service is not injected")
