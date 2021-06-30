import re
from pathlib import Path
from typing import Union, Optional, Callable, Tuple

from antarest.common.config import Config
from antarest.common.custom_types import JSON, SUB_JSON
from antarest.common.jwt import DEFAULT_ADMIN_USER
from antarest.common.requests import RequestParameters
from antarest.matrixstore.service import MatrixService
from antarest.storage.model import DEFAULT_WORKSPACE_NAME


class UriResolverService:
    def __init__(self, config: Config, matrix_service: MatrixService):
        self.config = config
        self.matrix_service = matrix_service

    def resolve(self, uri: str) -> Union[bytes, SUB_JSON]:
        match = re.match(r"^(\w+)://([\w-]+)$", uri)
        if not match:
            return None

        protocol = match.group(1)
        uuid = match.group(2)

        if protocol == "matrix":
            return self._resolve_matrix(uuid)
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

    def build_matrix_uri(self, id: str) -> str:
        return f"matrix://{id}"
