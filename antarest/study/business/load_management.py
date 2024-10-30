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

from antarest.core.model import JSON
from antarest.core.serialization import AntaresBaseModel
from antarest.study.model import MatrixFormat, Study
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix
from antarest.study.storage.storage_service import StudyStorageService

LOAD_PATH = "input/load/series/load_{area_id}"

class LoadInfoDTO(AntaresBaseModel):
    matrix: JSON | bytes


class LoadManager:
    def __init__(self, storage_service: StudyStorageService) -> None:
        self.storage_service = storage_service

    def get_load_matrix(self, study: Study, area_id: str, matrix_format: MatrixFormat) -> LoadInfoDTO:
        load_path = LOAD_PATH.replace("{area_id}", area_id).split("/")
        file_study = self.storage_service.get_storage(study).get_raw(study)

        node = file_study.tree.get_node(load_path)

        if isinstance(node, InputSeriesMatrix):
            if matrix_format == MatrixFormat.JSON:
                matrix_json = cast(JSON, InputSeriesMatrix.parse(node))
                return LoadInfoDTO(matrix = matrix_json)
            elif matrix_format == MatrixFormat.ARROW:
                matrix_df: pd.DataFrame = cast(pd.DataFrame, InputSeriesMatrix.parse(node, return_dataframe=True))
                with io.BytesIO() as buffer:
                    matrix_df.columns = matrix_df.columns.map(str)
                    matrix_df.to_feather(buffer, compression="uncompressed")
                    return LoadInfoDTO(matrix = buffer.getvalue())