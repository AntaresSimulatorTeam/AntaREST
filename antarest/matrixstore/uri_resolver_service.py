import re
from typing import Optional, Tuple

import pandas as pd  # type: ignore

from antarest.core.model import JSON, SUB_JSON
from antarest.matrixstore.service import ISimpleMatrixService


class UriResolverService:
    def __init__(self, matrix_service: ISimpleMatrixService):
        self.matrix_service = matrix_service

    def resolve(self, uri: str, formatted: bool = True) -> Optional[SUB_JSON]:
        res = UriResolverService._extract_uri_components(uri)
        if res:
            protocol, uuid = res
        else:
            return None

        if protocol == "matrix":
            return self._resolve_matrix(uuid, formatted)
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

    def _resolve_matrix(self, id: str, formatted: bool = True) -> SUB_JSON:
        data = self.matrix_service.get(id)
        if data:
            formatted_data = {
                "data": data.data,
                "index": data.index,
                "columns": data.columns,
            }
            if formatted:
                return formatted_data
            else:
                df = pd.DataFrame(**formatted_data)
                if not df.empty:
                    return (
                        df.to_csv(
                            None,
                            sep="\t",
                            header=False,
                            index=False,
                            float_format="%.6f",
                        )
                        or ""
                    )
                else:
                    return ""
        raise ValueError(f"id matrix {id} not found")

    def build_matrix_uri(self, id: str) -> str:
        return f"matrix://{id}"
