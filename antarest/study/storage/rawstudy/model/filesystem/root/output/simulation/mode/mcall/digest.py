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

from typing import List, Optional, cast

import pandas as pd
from pydantic import Field
from typing_extensions import override

from antarest.core.model import JSON
from antarest.core.serde import AntaresBaseModel
from antarest.matrixstore.uri_resolver_service import MatrixUriMapper
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.mcall.synthesis import OutputSynthesis


class DigestMatrixUI(AntaresBaseModel):
    columns: List[str | List[str]]
    data: List[List[str]]
    grouped_columns: bool = Field(alias="groupedColumns")


class DigestUI(AntaresBaseModel):
    area: DigestMatrixUI
    districts: DigestMatrixUI
    flow_linear: DigestMatrixUI = Field(alias="flowLinear")
    flow_quadratic: DigestMatrixUI = Field(alias="flowQuadratic")


def _get_flow_linear(df: pd.DataFrame) -> DigestMatrixUI:
    return _get_flow(df, "Links (FLOW LIN.)")


def _get_flow_quadratic(df: pd.DataFrame) -> DigestMatrixUI:
    return _get_flow(df, "Links (FLOW QUAD.)")


def _get_flow(df: pd.DataFrame, keyword: str) -> DigestMatrixUI:
    first_column = df["1"].tolist()
    index = next((k for k, v in enumerate(first_column) if v == keyword), None)
    if not index:
        return DigestMatrixUI(columns=[], data=[], groupedColumns=False)
    index_start = index + 2
    df_col_start = 1
    df_size = next((k for k, v in enumerate(first_column[index_start:]) if v == ""), len(first_column) - index_start)
    flow_df = df.iloc[index_start : index_start + df_size, df_col_start : df_col_start + df_size]
    data = flow_df.iloc[1:, :].to_numpy().tolist()
    cols = [""] + flow_df.iloc[0, 1:].tolist()
    return DigestMatrixUI(columns=cols, data=data, groupedColumns=False)


def _build_areas_and_districts(df: pd.DataFrame, first_row: int) -> DigestMatrixUI:
    first_column = df["1"].tolist()
    first_area_row = df.iloc[first_row, 2:].tolist()
    col_number = next((k for k, v in enumerate(first_area_row) if v == ""), df.shape[1])
    final_index = first_column[first_row:].index("") + first_row
    data = df.iloc[first_row:final_index, 1 : col_number + 1].to_numpy().tolist()
    cols_raw = df.iloc[first_row - 3 : first_row, 2 : col_number + 1].to_numpy().tolist()
    columns = [[""]] + [[a, b, c] for a, b, c in zip(cols_raw[0], cols_raw[1], cols_raw[2])]
    return DigestMatrixUI(columns=columns, data=data, groupedColumns=True)


def _get_area(df: pd.DataFrame) -> DigestMatrixUI:
    return _build_areas_and_districts(df, 7)


def _get_district(df: pd.DataFrame) -> DigestMatrixUI:
    first_column = df["1"].tolist()
    first_row = next((k for k, v in enumerate(first_column) if "@" in v), None)
    if not first_row:
        return DigestMatrixUI(columns=[], data=[], groupedColumns=False)
    return _build_areas_and_districts(df, first_row)


class DigestSynthesis(OutputSynthesis):
    def __init__(self, matrix_mapper: MatrixUriMapper, config: FileStudyTreeConfig):
        super().__init__(matrix_mapper, config)

    @override
    def load(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
        formatted: bool = True,
    ) -> JSON:
        df = self._parse_digest_file()

        output = df.to_dict(orient="split")
        del output["index"]
        return cast(JSON, output)

    def get_ui(self) -> DigestUI:
        """
        Parse a digest file and returns it as 4 separated matrices.
        One for areas, one for the districts, one for linear flow and the last one for quadratic flow.
        """
        df = self._parse_digest_file()
        flow_linear = _get_flow_linear(df)
        flow_quadratic = _get_flow_quadratic(df)
        area = _get_area(df)
        districts = _get_district(df)
        return DigestUI(area=area, districts=districts, flowLinear=flow_linear, flowQuadratic=flow_quadratic)

    def _parse_digest_file(self) -> pd.DataFrame:
        """
        Parse a digest file as a whole and return a single DataFrame.

        The `digest.txt` file is a TSV file containing synthetic results of the simulation.
        This file contains several data tables, each being separated by empty lines
        and preceded by a header describing the nature and dimensions of the table.

        Note that rows in the file may have different number of columns.
        """
        with open(self.config.path, "r") as digest_file:
            # Reads the file and find the maximum number of columns in any row
            data = [row.split("\t") for row in digest_file.read().splitlines()]
            max_cols = max(len(row) for row in data)

            # Adjust the number of columns in each row
            data = [row + [""] * (max_cols - len(row)) for row in data]

            # Returns a DataFrame from the data (do not convert values to float)
            df = pd.DataFrame(data=data, columns=[str(i) for i in range(max_cols)], dtype=object)
            return df
