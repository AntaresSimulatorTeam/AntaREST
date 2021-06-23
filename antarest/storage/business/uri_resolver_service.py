import re
from pathlib import Path

from antarest.common.config import Config
from antarest.common.jwt import JWTUser, JWTGroup
from antarest.common.requests import RequestParameters
from antarest.common.roles import RoleType
from antarest.login.model import User
from antarest.storage.service import StorageService


class UriResolverService:
    ADMIN = RequestParameters(
        user=JWTUser(
            id=1,
            impersonator=1,
            type="user",
            groups=[JWTGroup(id="admin", name="admin", role=RoleType.ADMIN)],
        )
    )

    def __init__(self, storage_service: StorageService, config: Config):
        self.config = config
        self.storage_service = storage_service

    def resolve(self, uri: str):
        match = re.match(r"^(\w+):\/\/([\w-]+)\/?(.*)$", uri)
        if not match:
            return

        protocol = match.group(1)
        id = match.group(2)
        path = match.group(3)

        if protocol == "studyfile":
            self._resolve_studyfile(id, path)

    def _resolve_studyfile(self, id: str, path: str):
        pass

    def _get_path(self, study_id: str) -> Path:
        return self.storage_service.get_study_path(
            study_id, UriResolverService.ADMIN
        )
