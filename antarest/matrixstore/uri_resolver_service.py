# Copyright (c) 2025, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import re
from typing import Optional, Tuple

import pandas as pd

from antarest.core.model import JSON
from antarest.matrixstore.service import ISimpleMatrixService


class UriResolverService:
    def __init__(self, matrix_service: ISimpleMatrixService):
        self.matrix_service = matrix_service

    def resolve(self, uri: str, formatted: bool = True) -> JSON | str | None:
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

    def _resolve_matrix(self, id: str, formatted: bool = True) -> JSON | str:
        data = self.matrix_service.get(id)
        if not data:
            raise ValueError(f"id matrix {id} not found")
        if data.data == [[]]:
            # Corresponds to an empty matrix, so we should return empty index and columns.
            data.columns = []
            data.index = []

        if formatted:
            return {
                "data": data.data,
                "index": data.index,
                "columns": data.columns,
            }
        df = pd.DataFrame(
            data=data.data,
            index=data.index,
            columns=data.columns,
        )
        if df.empty:
            return ""
        csv = df.to_csv(
            None,
            sep="\t",
            header=False,
            index=False,
            float_format="%.6f",
        )
        return csv or ""

    def build_matrix_uri(self, id: str) -> str:
        return f"matrix://{id}"
