import re
from typing import Union

from antarest.core.config import Config
from antarest.core.custom_types import JSON, SUB_JSON
from antarest.matrixstore.service import MatrixService, ISimpleMatrixService


class UriResolverService:
    def __init__(self, matrix_service: ISimpleMatrixService):
        self.matrix_service = matrix_service

    def resolve(self, uri: str) -> Union[bytes, SUB_JSON]:
        match = re.match(r"^(\w+)://(.+)$", uri)
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
