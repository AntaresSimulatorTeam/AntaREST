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
from io import BytesIO
from typing import cast

import pandas as pd
from starlette.responses import Response

from antarest.study.business.model.load_model import LoadDTO
from antarest.study.model import Study
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix
from antarest.study.storage.storage_service import StudyStorageService

LOAD_PATH = "input/load/series/load_{area_id}"


class LoadManager:
    def __init__(self, storage_service: StudyStorageService) -> None:
        self.storage_service = storage_service

    def get_load_matrix(self, study: Study, area_id: str) -> pd.DataFrame:
        file_study = self.storage_service.get_storage(study).get_raw(study)

        load_path = LOAD_PATH.format(area_id=area_id).split("/")
        node = file_study.tree.get_node(load_path)

        if not isinstance(node, InputSeriesMatrix):
            raise ValueError("Invalid node type")

        matrix_data = InputSeriesMatrix.parse(node, return_dataframe=True)

        matrix_df = cast(pd.DataFrame, matrix_data)
        matrix_df.columns = matrix_df.columns.map(str)

        return matrix_df

    def update_load_matrix(self, study: Study, area_id: str, load_dto: LoadDTO) -> LoadDTO:
        load_properties = load_dto.to_properties()
        load_path = LOAD_PATH.format(area_id=area_id).split("/")

        file_study = self.storage_service.get_storage(study).get_raw(study)

        df = pd.read_feather(BytesIO(load_properties.matrix))

        if df.shape[1] != 2:
            pass

        file_study.tree.save(load_properties.matrix, load_path)

        return load_dto
