import re
from pathlib import Path

from antarest.common.config import Config
from antarest.common.jwt import JWTUser, JWTGroup, DEFAULT_ADMIN_USER
from antarest.common.requests import RequestParameters
from antarest.common.roles import RoleType
from antarest.login.model import User
from antarest.storage.model import DEFAULT_WORKSPACE_NAME


class UriResolverService:
    def __init__(self, config: Config):
        self.config = config
        self.storage_service = None

    def resolve(self, uri: str):
        match = re.match(r"^(\w+):\/\/([\w-]+)\/?(.*)$", uri)
        if not match:
            return

        protocol = match.group(1)
        id = match.group(2)
        path = match.group(3)

        if protocol == "studyfile":
            self._resolve_studyfile(id, path)

    def _resolve_studyfile(self, id: str, path: str) -> Path:
        return self._get_path(id) / path

    def _get_path(self, study_id: str) -> Path:
        return self.storage_service.get_study_path(
            study_id, DEFAULT_ADMIN_USER
        )

    def build_studyfile_uri(self, path: Path, study_id: str) -> str:
        relative_path = str(path.absolute()).split(f"{study_id}/")[1]
        uri = f"studyfile://{study_id}/{relative_path}"
        return uri

    def build_matrix_uri(self, id) -> str:
        return f"matrix://{id}"

    def is_managed(self, study_id) -> bool:
        default = self.config.storage.workspaces[DEFAULT_WORKSPACE_NAME]
        return default in self.storage_service.get_study_path(study_id).parts
