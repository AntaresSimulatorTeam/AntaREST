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
import logging
from pathlib import Path
from typing import Any, Dict, Iterator, List, MutableSequence, Optional, Sequence

import numpy as np
import pandas as pd
import polars as pl
from polars.exceptions import ComputeError

from antarest.core.exceptions import MCRootNotHandled, OutputAggregationError, OutputNotFound, OutputSubFolderNotFound
from antarest.study.business.output.utils import (
    MCYEAR_COL,
    MCAllAreasQueryFile,
    MCIndAreasQueryFile,
    MCIndLinksQueryFile,
    MCRoot,
    QueryFileType,
    get_start_column,
    normalize_df_column_names,
    parse_headers,
)
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency

# noinspection SpellCheckingInspection
AREA_COL = "area"
"""Column name for the area."""
LINK_COL = "link"
"""Column name for the link."""
TIME_ID_COL = "timeId"
"""Column name for the time index."""
CLUSTER_ID_COL = "cluster"
"""Column name for the cluster id."""
MC_YEAR_INDEX = 0
"""Index in path parts starting from the Monte Carlo year to determine the Monte Carlo year."""
AREA_OR_LINK_INDEX__IND, AREA_OR_LINK_INDEX__ALL = 2, 1
"""Indexes in path parts starting from the output root `economy//mc-(ind/all)` to determine the area/link name."""
CLUSTER_ID_COMPONENT = 0
ACTUAL_COLUMN_COMPONENT = 1
DUMMY_COMPONENT = 2

logger = logging.getLogger(__name__)


def _columns_ordering(df_cols: List[str], column_name: str, is_details: bool, mc_root: MCRoot) -> Sequence[str]:
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


def _infer_time_id(df: pd.DataFrame, is_details: bool) -> List[int]:
    if is_details:
        return df[TIME_ID_COL].tolist()
    else:
        return list(range(1, len(df) + 1))


def _filtered_files_listing(
    folders_to_check: List[Path],
    query_file: str,
    frequency: str,
) -> Dict[str, MutableSequence[str]]:
    filtered_files: Dict[str, MutableSequence[str]] = {}
    for folder_path in folders_to_check:
        for file in folder_path.iterdir():
            if file.stem == f"{query_file}-{frequency}":
                filtered_files.setdefault(folder_path.name, []).append(file.name)
    return filtered_files


class AggregatorManager:
    def __init__(
        self,
        output_path: Path,
        query_file: QueryFileType,
        frequency: MatrixFrequency,
        ids_to_consider: Sequence[str],
        columns_names: Sequence[str],
        mc_years: Optional[Sequence[int]] = None,
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
        self.mc_ind_path = self.output_path / "economy" / MCRoot.MC_IND.value
        self.mc_all_path = self.output_path / "economy" / MCRoot.MC_ALL.value
        self.mc_root = (
            MCRoot.MC_IND
            if (isinstance(query_file, MCIndAreasQueryFile) or isinstance(query_file, MCIndLinksQueryFile))
            else MCRoot.MC_ALL
        )
        self._output_first_column = get_start_column(self.frequency)

    def _parse_output_file(self, file_path: Path, normalize_column_names: bool) -> pd.DataFrame:
        content = file_path.read_text(encoding="utf-8")
        output_headers = parse_headers(content, self._output_first_column)
        try:
            polars_df = pl.read_csv(
                file_path, skip_lines=7, separator="\t", has_header=False, null_values="N/A", n_threads=1
            )
        except ComputeError:
            # Happens if polars wrongly inferred the schema. If so, we specify that he shouldn't try.
            # This way the parsing does not fail, but it is significantly slower.
            # This case does not seem to happen very often.
            polars_df = pl.read_csv(
                file_path,
                skip_lines=7,
                separator="\t",
                has_header=False,
                null_values="N/A",
                infer_schema=False,
                n_threads=1,
            )

        df = polars_df[polars_df.columns[self._output_first_column :]].to_pandas().astype(np.float64)

        df.columns = pd.MultiIndex.from_tuples(output_headers)  # type: ignore

        if normalize_column_names:
            df.columns = pd.Index(normalize_df_column_names(self.mc_root, output_headers))

        return df

    def _filter_ids(self, folder_path: Path) -> List[str]:
        if self.output_type == "areas":
            # Areas names filtering
            areas_ids = sorted([d.name for d in folder_path.iterdir()])
            if self.ids_to_consider:
                areas_ids = [area_id for area_id in areas_ids if area_id in self.ids_to_consider]
            return areas_ids

        # Links names filtering
        links_ids = sorted(d.name for d in folder_path.iterdir())
        if self.ids_to_consider:
            return [link for link in links_ids if link in self.ids_to_consider]
        return links_ids

    def _gather_all_files_to_consider(self) -> Sequence[Path]:
        if self.mc_root == MCRoot.MC_IND:
            # Monte Carlo years filtering
            all_mc_years = [d.name for d in self.mc_ind_path.iterdir()]
            if self.mc_years:
                all_mc_years = [year for year in all_mc_years if int(year) in self.mc_years]
            if not all_mc_years:
                return []

            # Links / Areas ids filtering

            # The list of areas and links is the same whatever the MC year under consideration:
            # Therefore we choose the first year by default avoiding useless scanning directory operations.
            first_mc_year = all_mc_years[0]
            areas_or_links_ids = self._filter_ids(self.mc_ind_path / first_mc_year / self.output_type)

            # Frequency and query file filtering
            folders_to_check = [self.mc_ind_path / first_mc_year / self.output_type / id for id in areas_or_links_ids]
            filtered_files = _filtered_files_listing(folders_to_check, self.query_file, self.frequency)

            # Loop on MC years to return the whole list of files
            all_output_files = [
                self.mc_ind_path / mc_year / self.output_type / area_or_link / file
                for mc_year in all_mc_years
                for area_or_link, files in filtered_files.items()
                for file in files
            ]
        elif self.mc_root == MCRoot.MC_ALL:
            # Links / Areas ids filtering
            areas_or_links_ids = self._filter_ids(self.mc_all_path / self.output_type)

            # Frequency and query file filtering
            folders_to_check = [self.mc_all_path / self.output_type / id for id in areas_or_links_ids]
            filtered_files = _filtered_files_listing(folders_to_check, self.query_file, self.frequency)

            # Loop to return the whole list of files
            all_output_files = [
                self.mc_all_path / self.output_type / area_or_link / file
                for area_or_link, files in filtered_files.items()
                for file in files
            ]
        else:
            raise MCRootNotHandled(f"Unknown Monte Carlo root: {self.mc_root}")
        return all_output_files

    def columns_filtering(self, df: pd.DataFrame, is_details: bool) -> pd.DataFrame:
        # columns filtering
        lower_case_columns = [c.lower() for c in self.columns_names]
        if lower_case_columns:
            if is_details:
                filtered_columns = [CLUSTER_ID_COL, TIME_ID_COL] + [
                    c for c in df.columns.tolist() if any(regex in c.lower() for regex in lower_case_columns)
                ]
            elif self.mc_root == MCRoot.MC_ALL:
                filtered_columns = [
                    c for c in df.columns.tolist() if any(regex in c.lower() for regex in lower_case_columns)
                ]
            else:
                filtered_columns = [c for c in df.columns.tolist() if c.lower() in lower_case_columns]
            df = df.loc[:, filtered_columns]
        return df

    def _process_df(self, file_path: Path, is_details: bool) -> pd.DataFrame:
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

        df = self._parse_output_file(file_path, normalize_column_names=not is_details)
        if not is_details:
            return df

        # number of rows in the data frame
        df_len = len(df)
        cluster_dummy_product_cols = sorted(set([(x[CLUSTER_ID_COMPONENT], x[DUMMY_COMPONENT]) for x in df.columns]))
        # actual columns without the cluster id (NODU, production etc.)
        actual_cols = sorted(set(df.columns.map(lambda x: x[ACTUAL_COLUMN_COMPONENT])))

        # using a dictionary to build the new data frame with the base columns (NO2, production etc.)
        # and the cluster id and time id
        new_obj: Dict[str, Any] = {k: [] for k in [CLUSTER_ID_COL, TIME_ID_COL] + actual_cols}

        # loop over the cluster id to extract the values of the actual columns
        for cluster_id, dummy_component in cluster_dummy_product_cols:
            for actual_col in actual_cols:
                col_values = df[(cluster_id, actual_col, dummy_component)].tolist()
                new_obj[actual_col] += col_values
            new_obj[CLUSTER_ID_COL] += [cluster_id for _ in range(df_len)]
            new_obj[TIME_ID_COL] += list(range(1, df_len + 1))

        # reorganize the data frame
        columns_order = [CLUSTER_ID_COL, TIME_ID_COL] + list(actual_cols)
        final_df = pd.DataFrame(new_obj).reindex(columns=columns_order).sort_values(by=[TIME_ID_COL, CLUSTER_ID_COL])

        return final_df

    def _build_dataframes(self, files: Sequence[Path]) -> Iterator[pd.DataFrame]:
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
            df = self._process_df(file_path, is_details)

            # columns filtering
            df = self.columns_filtering(df, is_details)

            column_name = AREA_COL if self.output_type == "areas" else LINK_COL
            new_column_order = _columns_ordering(df.columns.tolist(), column_name, is_details, self.mc_root)

            if self.mc_root == MCRoot.MC_IND:
                # add column for links/areas
                relative_path_parts = file_path.relative_to(self.mc_ind_path).parts
                df[column_name] = relative_path_parts[AREA_OR_LINK_INDEX__IND]
                # add column to record the Monte Carlo year
                df[MCYEAR_COL] = int(relative_path_parts[MC_YEAR_INDEX])
            else:
                # add column for links/areas
                relative_path_parts = file_path.relative_to(self.mc_all_path).parts
                df[column_name] = relative_path_parts[AREA_OR_LINK_INDEX__ALL]

            # add a column for the time id
            df[TIME_ID_COL] = _infer_time_id(df, is_details)
            # Reorganize the columns
            df = df.reindex(columns=pd.Index(new_column_order))

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

    def aggregate_output_data(self) -> Iterator[pd.DataFrame]:
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
        all_output_files = sorted(self._gather_all_files_to_consider())

        if not all_output_files:
            raise OutputAggregationError(self.output_id, "No output files matching the criteria were found.")

        logger.info(
            f"Parsing {len(all_output_files)} {self.frequency.value} files"
            f"to build the aggregated output {self.output_id}"
        )
        # builds final dataframe
        return self._build_dataframes(all_output_files)
