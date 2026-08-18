# Copyright (c) 2026, RTE (https://www.rte-france.com)
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
import logging
import warnings
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import TypeAlias

import pandas as pd
import polars as pl

from antarest.core.exceptions import MCRootNotHandled, OutputAggregationError, OutputNotFound, OutputSubFolderNotFound
from antarest.output.filestudy.iteration import select_files
from antarest.output.filestudy.matrixfiles import get_start_column, parse_output_file
from antarest.output.filestudy.model import (
    MCYEAR_COL,
    TIME_ID_COL,
    MCAllAreasQueryFile,
    MCIndAreasQueryFile,
    MCIndLinksQueryFile,
    MCRoot,
    OutputDataFrame,
    QueryFileType,
    VariableDescription,
)
from antarest.output.utils import find_mode_dir
from antarest.study.model import MatrixFrequency

# We use pandas.DataFrame.stack() without the `future_stack` keyword as its 2 times faster
# But it logs a FutureWarning every time so we silence it here.
warnings.simplefilter(action="ignore", category=FutureWarning)

# noinspection SpellCheckingInspection
AREA_COL = "area"
"""Column name for the area."""
LINK_COL = "link"
"""Column name for the link."""
CLUSTER_ID_COL = "cluster"
"""Column name for the cluster id."""
MC_YEAR_INDEX = 0
"""Index in path parts starting from the Monte Carlo year to determine the Monte Carlo year."""
AREA_OR_LINK_INDEX__IND, AREA_OR_LINK_INDEX__ALL = 2, 1
"""Indexes in path parts starting from the output root `economy//mc-(ind/all)` to determine the area/link name."""
CLUSTER_ID_COMPONENT = 0
ACTUAL_COLUMN_COMPONENT = 1

logger = logging.getLogger(__name__)

# The implementation uses sometimes plain string headers,
# sometimes a tuple of strings (name, unit, stat)
# Typing should be improved, but for now we stick with that union.
ColMetadata: TypeAlias = VariableDescription | str


def _check_is_str(value: ColMetadata) -> str:
    if not isinstance(value, str):
        raise ValueError(f"Expected a string, got {type(value)}")
    return value


def _columns_ordering(df_cols: list[str], column_name: str, is_details: bool, mc_root: MCRoot) -> list[str]:
    # original columns
    org_cols = df_cols.copy()
    if is_details:
        org_cols = [col for col in org_cols if col != CLUSTER_ID_COL and col != TIME_ID_COL]
    if mc_root == MCRoot.MC_IND:
        new_column_order = (
            [column_name] + ([CLUSTER_ID_COL] if is_details else []) + [MCYEAR_COL, TIME_ID_COL] + org_cols
        )
    elif mc_root == MCRoot.MC_ALL:
        org_cols = [col for col in org_cols if col not in {column_name, MCYEAR_COL}]
        new_column_order = [column_name] + ([CLUSTER_ID_COL] if is_details else []) + [TIME_ID_COL] + org_cols
    else:
        raise MCRootNotHandled(f"Unknown Monte Carlo root: {mc_root}")

    return new_column_order


class AggregatorManager:
    def __init__(
        self,
        output_path: Path,
        query_file: QueryFileType,
        frequency: MatrixFrequency,
        ids_to_consider: Sequence[str],
        columns_names: Sequence[str],
        mc_years: Sequence[int] | None = None,
    ):
        self.output_path = output_path
        self.output_id = self.output_path.name
        self.query_file = query_file
        self.frequency = frequency
        self.mc_years = mc_years
        self.columns_names = columns_names
        self.ids_to_consider = ids_to_consider
        self.output_type = (
            "areas"
            if (isinstance(query_file, MCIndAreasQueryFile) or isinstance(query_file, MCAllAreasQueryFile))
            else "links"
        )
        _mode_dir = find_mode_dir(self.output_path)
        if _mode_dir is None:
            raise OutputSubFolderNotFound(self.output_id, f"economy/{MCRoot.MC_IND.value}")
        self.mc_ind_path = _mode_dir / MCRoot.MC_IND.value
        self.mc_all_path = _mode_dir / MCRoot.MC_ALL.value
        self.mc_root = (
            MCRoot.MC_IND
            if (isinstance(query_file, MCIndAreasQueryFile) or isinstance(query_file, MCIndLinksQueryFile))
            else MCRoot.MC_ALL
        )
        self._output_first_column = get_start_column(self.frequency)

    def _parse_output_file(self, file_path: Path, normalize_column_names: bool) -> OutputDataFrame[ColMetadata]:
        output_data = parse_output_file(file_path, self._output_first_column)

        def convert_metadata(var: VariableDescription) -> ColMetadata:
            if normalize_column_names:
                return var.normal_repr()
            return var

        return output_data.map_metadata(convert_metadata)

    def _variable_names(self, headers: list[ColMetadata]) -> list[str]:
        return [col.name if isinstance(col, VariableDescription) else col for col in headers]

    def columns_filtering(self, data: OutputDataFrame[ColMetadata], is_details: bool) -> OutputDataFrame[ColMetadata]:
        # columns filtering
        lower_case_columns = [c.lower() for c in self.columns_names]
        if lower_case_columns:
            df_columns = self._variable_names(data.headers)
            if self.mc_root == MCRoot.MC_ALL:
                filtered_columns = [c for c in df_columns if any(regex in c.lower() for regex in lower_case_columns)]
            else:
                filtered_columns = [c for c in df_columns if c.lower() in lower_case_columns]

            if is_details:
                filtered_columns.insert(0, TIME_ID_COL)
                filtered_columns.insert(0, CLUSTER_ID_COL)

            indices = [k for k, c in enumerate(df_columns) if c in filtered_columns]
            data.data = data.data.select([data.data.columns[i] for i in indices])
            data.headers = [data.headers[i] for i in indices]

        return data

    def _process_df(self, file_path: Path, is_details: bool) -> OutputDataFrame[ColMetadata]:
        """
        Process the output file to return a DataFrame with the correct columns and values
            - In the case of a details file, the DataFrame, the columns include two parts cluster name + actual column name
            - In other cases, the DataFrame, the columns include only the actual column name

        Thus, the DataFrame is normalized to have the real columns names in both cases. And a new column is added to
        for the details file to record the cluster id.

        Args:
            file_path: the file Path to extract the data Frame from
            is_details: whether the file is a details file or not

        Returns:
            the DataFrame with the correct columns and values
        """
        normalize_cols = not is_details
        output_data = self._parse_output_file(file_path, normalize_column_names=normalize_cols)
        if not is_details:
            return output_data

        df = output_data.data.to_pandas()
        df.columns = pd.MultiIndex.from_tuples(output_data.headers)  # type: ignore
        nb_clusters = df.columns.get_level_values(CLUSTER_ID_COMPONENT).nunique()
        # actual columns without the cluster id (NODU, production etc.)
        actual_cols = sorted(df.columns.get_level_values(ACTUAL_COLUMN_COMPONENT).unique())

        # First perform the stack / unstack operation to have the final shape
        final_df = df.stack(level=[CLUSTER_ID_COMPONENT, ACTUAL_COLUMN_COMPONENT]).unstack()
        assert isinstance(final_df, pd.DataFrame)

        # Reset the index, drop the first column and rename the columns accordingly
        final_df.reset_index(inplace=True)
        final_df.drop(final_df.columns[0], axis=1, inplace=True)
        final_df.columns = pd.Index([CLUSTER_ID_COL] + actual_cols, dtype="str")

        # Add the TIME_ID column and reindex to have the columns in the right order
        final_df[TIME_ID_COL] = (final_df.index // nb_clusters) + 1
        pandas_df = final_df.reindex(columns=[CLUSTER_ID_COL, TIME_ID_COL] + list(actual_cols))
        return OutputDataFrame(headers=pandas_df.columns.tolist(), data=pl.DataFrame(pandas_df))

    def _build_dataframes(self, files: Sequence[Path]) -> Iterator[pl.DataFrame]:
        if self.mc_root not in [MCRoot.MC_IND, MCRoot.MC_ALL]:
            raise MCRootNotHandled(f"Unknown Monte Carlo root: {self.mc_root}")
        is_details = self.query_file in [
            MCIndAreasQueryFile.DETAILS,
            MCAllAreasQueryFile.DETAILS,
            MCIndAreasQueryFile.DETAILS_ST_STORAGE,
            MCAllAreasQueryFile.DETAILS_ST_STORAGE,
            MCIndAreasQueryFile.DETAILS_RES,
            MCAllAreasQueryFile.DETAILS_RES,
        ]

        for k, file_path in enumerate(files):
            output_data = self._process_df(file_path, is_details)

            # columns filtering
            output_data = self.columns_filtering(output_data, is_details)

            # Starting from here, output_data.headers are just a list of strings.
            # We can use them as columns for our dataframe.
            df = output_data.data
            df.columns = output_data.map_metadata(_check_is_str).headers

            column_name = AREA_COL if self.output_type == "areas" else LINK_COL
            new_column_order = _columns_ordering(df.columns, column_name, is_details, self.mc_root)

            if self.mc_root == MCRoot.MC_IND:
                # add column for links/areas
                relative_path_parts = file_path.relative_to(self.mc_ind_path).parts
                data = relative_path_parts[AREA_OR_LINK_INDEX__IND]
                df = df.with_columns(pl.lit(data).alias(column_name))

                # add column to record the Monte Carlo year
                value = int(relative_path_parts[MC_YEAR_INDEX])
                df = df.with_columns(pl.lit(value).alias(MCYEAR_COL))
            else:
                # add column for links/areas
                relative_path_parts = file_path.relative_to(self.mc_all_path).parts
                data = relative_path_parts[AREA_OR_LINK_INDEX__ALL]
                df = df.with_columns(pl.lit(data).alias(column_name))

            # add a column for the time id
            if not is_details:
                df = df.with_row_index(TIME_ID_COL, offset=1)

            # Reorganize the columns
            df = df.select(new_column_order)

            yield df

    def _check_mc_root_folder_exists(self) -> None:
        if self.mc_root == MCRoot.MC_IND:
            if not self.mc_ind_path.exists():
                raise OutputSubFolderNotFound(self.output_id, f"economy/{MCRoot.MC_IND.value}")
        elif self.mc_root == MCRoot.MC_ALL:
            if not self.mc_all_path.exists():
                raise OutputSubFolderNotFound(self.output_id, f"economy/{MCRoot.MC_ALL.value}")
        else:
            raise MCRootNotHandled(f"Unknown Monte Carlo root: {self.mc_root}")

    def aggregate_output_data(self) -> Iterator[pl.DataFrame]:
        """
        Aggregates the output data of a study and returns it as a DataFrame
        """

        output_folder = (self.mc_ind_path or self.mc_all_path).parent.parent

        # checks if the output folder exists
        if not output_folder.exists():
            raise OutputNotFound(self.output_id)

        # checks if the mc root folder exists
        self._check_mc_root_folder_exists()

        # filters files to consider
        all_output_files = sorted(
            f.path
            for f in select_files(
                self.output_path, self.query_file, self.frequency, self.ids_to_consider, self.mc_years
            )
        )

        if not all_output_files:
            raise OutputAggregationError(self.output_id, "No output files matching the criteria were found.")

        logger.info(
            f"Parsing {len(all_output_files)} {self.frequency.value} files"
            f"to build the aggregated output {self.output_id}"
        )
        # builds final dataframe
        return self._build_dataframes(all_output_files)
