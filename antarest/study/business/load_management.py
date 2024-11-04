# Copyright (c) 2024, RTE (https://www.rte-france.com)
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
import io
from typing import cast

import pandas as pd
from starlette.responses import JSONResponse, Response

from antarest.core.model import JSON
from antarest.study.model import MatrixFormat, Study
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix
from antarest.study.storage.storage_service import StudyStorageService

LOAD_PATH = "input/load/series/load_{area_id}"


class LoadManager:
    def __init__(self, storage_service: StudyStorageService) -> None:
        self.storage_service = storage_service

    def get_load_matrix(self, study: Study, area_id: str, matrix_format: MatrixFormat) -> Response:
        file_study = self.storage_service.get_storage(study).get_raw(study)

        load_path = LOAD_PATH.format(area_id=area_id).split("/")
        node = file_study.tree.get_node(load_path)

        if not isinstance(node, InputSeriesMatrix):
            return Response(content="Invalid node type", status_code=400)

        matrix_data = InputSeriesMatrix.parse(node, return_dataframe=(matrix_format == MatrixFormat.ARROW))

        if matrix_format == MatrixFormat.JSON:
            return JSONResponse(content=cast(JSON, matrix_data))

        if matrix_format == MatrixFormat.ARROW:
            matrix_df = cast(pd.DataFrame, matrix_data)
            matrix_df.columns = matrix_df.columns.map(str)
            buffer = io.BytesIO()
            matrix_df.to_feather(buffer, compression="uncompressed")
            return Response(content=buffer.getvalue(), media_type="application/octet-stream")

        return Response(content="Unsupported format", status_code=422)
