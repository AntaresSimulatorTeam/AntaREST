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
import typing as t

from antarest.core.model import JSON
from antarest.core.serialization import AntaresBaseModel
from antarest.study.business.all_optional_meta import camel_case_model
from antarest.study.model import MatrixFormat, Study
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix
from antarest.study.storage.storage_service import StudyStorageService

LOAD_PATH = "input/load/series/load_{area_id}"

@camel_case_model
class LoadInfoDTO(AntaresBaseModel):
    matrix: JSON | bytes

class LoadCreationInfo(LoadInfoDTO):
    pass

class LoadManager:
    def __init__(self, storage_service: StudyStorageService) -> None:
        self.storage_service = storage_service

    def get_load_matrix(self, study: Study, area_id: str, matrix_format: MatrixFormat) -> LoadInfoDTO:
        load_path = LOAD_PATH.replace("{area_id}", area_id).split("/")
        file_study = self.storage_service.get_storage(study).get_raw(study)

        if matrix_format == MatrixFormat.JSON:
            node = file_study.tree.get_node(load_path)
            if isinstance(node, InputSeriesMatrix):
                matrix = InputSeriesMatrix.parse(node)
                return LoadInfoDTO(matrix=matrix)
        elif matrix_format == MatrixFormat.ARROW:
            pass

