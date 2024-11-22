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

import pandas as pd

from antarest.core.model import JSON
from antarest.core.serialization import AntaresBaseModel
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.mcall.synthesis import OutputSynthesis


class DigestMatrixDTO(AntaresBaseModel):
    rowHeaders: t.List[str]
    columns: t.List[str]
    data: t.List[t.List[t.Any]]
    grouped_columns: bool


class DigestDTO(AntaresBaseModel):
    area: DigestMatrixDTO
    districts: DigestMatrixDTO
    flow_linear: DigestMatrixDTO
    flow_quadratic: DigestMatrixDTO


def _get_flow_linear(df: pd.DataFrame) -> DigestMatrixDTO:
    return _get_flow(df, "Links (FLOW LIN.)")


def _get_flow_quadratic(df: pd.DataFrame) -> DigestMatrixDTO:
    return _get_flow(df, "Links (FLOW QUAD.)")


def _get_flow(df: pd.DataFrame, keyword: str) -> DigestMatrixDTO:
    first_column = df["1"].tolist()
    index = next((k for k, v in enumerate(first_column) if v == keyword), None)
    if not index:
        return DigestMatrixDTO(rowHeaders=[], columns=[], data=[], grouped_columns=False)
    index_start = index + 2
    df_col_start = 1
    df_size = next((k for k, v in enumerate(first_column[index_start:]) if v == ""), len(first_column) - index_start)
    flow_df = df.iloc[index_start : index_start + df_size, df_col_start : df_col_start + df_size]
    area_names = flow_df.iloc[0, 1:].tolist()
    data = flow_df.iloc[1:, 1:].to_numpy().tolist()
    return DigestMatrixDTO(rowHeaders=area_names, columns=area_names, data=data, grouped_columns=False)


def _build_areas_and_districts(df: pd.DataFrame, first_row: int) -> DigestMatrixDTO:
    first_column = df["1"].tolist()
    first_area_row = df.iloc[first_row, 2:].tolist()
    col_number = next((k for k, v in enumerate(first_area_row) if v == ""), df.shape[1])
    final_index = first_column[first_row:].index("") + first_row
    data = df.iloc[first_row:final_index, 2 : col_number + 1].to_numpy().tolist()
    index = first_column[first_row:final_index]
    # todo: retrun columns the same way the GET /raw does it
    return DigestMatrixDTO(rowHeaders=index, columns=[], data=data, grouped_columns=True)


def _get_area(df: pd.DataFrame) -> DigestMatrixDTO:
    return _build_areas_and_districts(df, 7)


def _get_district(df: pd.DataFrame) -> DigestMatrixDTO:
    first_column = df["1"].tolist()
    first_row = next((k for k, v in enumerate(first_column) if "@" in v), None)
    if not first_row:
        return DigestMatrixDTO(rowHeaders=[], columns=[], data=[], grouped_columns=False)
    return _build_areas_and_districts(df, first_row)


class DigestSynthesis(OutputSynthesis):
    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        super().__init__(context, config)

    def load(
        self,
        url: t.Optional[t.List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
        formatted: bool = True,
    ) -> JSON:
        df = self._parse_digest_file()

        output = df.to_dict(orient="split")
        del output["index"]
        return t.cast(JSON, output)

    def get_dto(self) -> DigestDTO:
        df = self._parse_digest_file()
        flow_linear = _get_flow_linear(df)
        flow_quadratic = _get_flow_quadratic(df)
        area = _get_area(df)
        districts = _get_district(df)
        return DigestDTO(area=area, districts=districts, flow_linear=flow_linear, flow_quadratic=flow_quadratic)

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
