import re
from typing import Optional, Tuple

import pandas as pd

from antarest.core.model import SUB_JSON
from antarest.matrixstore.service import ISimpleMatrixService


class UriResolverService:
    def __init__(self, matrix_service: ISimpleMatrixService):
        self.matrix_service = matrix_service

    def resolve(self, uri: str, format: str = "json") -> SUB_JSON:
        res = UriResolverService._extract_uri_components(uri)
        if res:
            protocol, uuid = res
        else:
            return None

        if protocol == "matrix":
            return self._resolve_matrix(uuid, format)
        raise NotImplementedError(f"protocol {protocol} not implemented")

    @staticmethod
    def _extract_uri_components(uri: str) -> Optional[Tuple[str, str]]:
        match = re.match(r"^(\w+)://(.+)$", uri)
        if not match:
            return None

        protocol = match.group(1)
        uuid = match.group(2)
        return protocol, uuid

    @staticmethod
    def extract_id(uri: str) -> Optional[str]:
        res = UriResolverService._extract_uri_components(uri)
        return res[1] if res else None

    def _resolve_matrix(self, id: str, format: str) -> SUB_JSON:
        data = self.matrix_service.get(id)
        if data:
            if format == "json":
                return {
                    "data": data.data,
                    "index": data.index,
                    "columns": data.columns,
                }
            else:
                df = pd.DataFrame(
                    data=data.data,
                    index=data.index,
                    columns=data.columns,
                )
                if df.empty:
                    return ""
                else:
                    csv = df.to_csv(
                        None,
                        sep="\t",
                        header=False,
                        index=False,
                        float_format="%.6f",
                    )
                    return csv or ""
        raise ValueError(f"id matrix {id} not found")

    def build_matrix_uri(self, id: str) -> str:
        return f"matrix://{id}"
