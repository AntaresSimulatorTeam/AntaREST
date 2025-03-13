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

import typing as t

import pandas as pd

from antarest.study.model import MatrixIndex, Study
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix
from antarest.study.storage.utils import get_start_date
from antarest.study.storage.variantstudy.model.command_context import CommandContext

LOAD_PATH = "input/load/series/load_{area_id}"
matrix_columns = ["ts-0"]


class LoadManager:
    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_load_matrix(self, study: Study, area_id: str) -> t.Tuple[pd.DataFrame, t.Dict[str | bytes, str | bytes]]:
        file_study = study.get_files()
        load_path = LOAD_PATH.format(area_id=area_id).split("/")

        node = file_study.tree.get_node(load_path)

        if not isinstance(node, InputSeriesMatrix):
            raise TypeError(f"Expected node of type 'InputSeriesMatrix', but got '{type(node).__name__}'")

        matrix_df = InputSeriesMatrix.parse_as_dataframe(node)

        matrix_df.columns = matrix_df.columns.map(str)

        matrix_df.columns = pd.Index(matrix_columns)

        matrix_index: MatrixIndex = get_start_date(file_study)

        metadata: t.Dict[str | bytes, str | bytes] = {
            "start_date": str(matrix_index.start_date),
            "steps": str(matrix_index.steps),
            "first_week_size": str(matrix_index.first_week_size),
            "level": str(matrix_index.level),
        }

        return matrix_df, metadata
