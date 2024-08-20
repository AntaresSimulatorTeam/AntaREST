import logging
import typing as t
from enum import Enum
from pathlib import Path

import numpy as np
import pandas as pd

from antarest.core.exceptions import FileTooLargeError, InvalidFieldForVersionError, OutputNotFound
from antarest.study.storage.rawstudy.ini_reader import IniReader
from antarest.study.storage.rawstudy.model.filesystem.matrix.date_serializer import (
    FactoryDateSerializer,
    rename_unnamed,
)
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency

MC_TEMPLATE_PARTS = "output/{sim_id}/economy/{mc_root}"
HORIZON_TEMPLATE = "output/{sim_id}/about-the-study/parameters.ini"
# noinspection SpellCheckingInspection
MCYEAR_COL = "mcYear"
"""Column name for the Monte Carlo year."""
AREA_COL = "area"
"""Column name for the area."""
LINK_COL = "link"
"""Column name for the link."""
TIME_ID_COL = "timeId"
"""Column name for the time index."""
TIME_COL = "time"
"""Column name for the timestamp."""
CLUSTER_ID_COL = "cluster"
"""Column name for the cluster id."""
MC_YEAR_INDEX = 0
"""Index in path parts starting from the Monte Carlo year to determine the Monte Carlo year."""
AREA_OR_LINK_INDEX__IND, AREA_OR_LINK_INDEX__ALL = 2, 1
"""Indexes in path parts starting from the output root `economy//mc-(ind/all)` to determine the area/link name."""
PRODUCTION_COLUMN_NAME = "production"
PRODUCTION_COLUMN_REGEX = "mwh"
CLUSTER_ID_COMPONENT = 0
ACTUAL_COLUMN_COMPONENT = 1
DUMMY_COMPONENT = 2

logger = logging.getLogger(__name__)


class MCRoot(str, Enum):
    MC_IND = "mc-ind"
    MC_ALL = "mc-all"


class MCIndAreasQueryFile(str, Enum):
    VALUES = "values"
    DETAILS = "details"
    DETAILS_ST_STORAGE = "details-STstorage"
    DETAILS_RES = "details-res"


class MCAllAreasQueryFile(str, Enum):
    VALUES = "values"
    DETAILS = "details"
    DETAILS_ST_STORAGE = "details-STstorage"
    DETAILS_RES = "details-res"
    ID = "id"


class MCIndLinksQueryFile(str, Enum):
    VALUES = "values"


class MCAllLinksQueryFile(str, Enum):
    VALUES = "values"
    ID = "id"


def _checks_estimated_size(nb_files: int, df_bytes_size: int, nb_files_checked: int) -> None:
    maximum_size = 100  # size in Mo that corresponds to a 15 seconds task.
    estimated_df_size = nb_files * df_bytes_size // (nb_files_checked * 10**6)
    if estimated_df_size > maximum_size:
        raise FileTooLargeError(estimated_df_size, maximum_size)


def _columns_ordering(df_cols: t.List[str], column_name: str, is_details: bool, mc_root: MCRoot) -> t.Sequence[str]:
    # original columns
    org_cols = df_cols.copy()
    if is_details:
        org_cols = [col for col in org_cols if col != CLUSTER_ID_COL and col != TIME_ID_COL]
    if mc_root == MCRoot.MC_IND:
        new_column_order = (
            [column_name] + ([CLUSTER_ID_COL] if is_details else []) + [MCYEAR_COL, TIME_ID_COL, TIME_COL] + org_cols
        )
    elif mc_root == MCRoot.MC_ALL:
        org_cols = [col for col in org_cols if col not in {column_name, MCYEAR_COL, TIME_COL}]
        new_column_order = [column_name] + ([CLUSTER_ID_COL] if is_details else []) + [TIME_ID_COL, TIME_COL] + org_cols
    else:
        raise InvalidFieldForVersionError(f"Unknown Monte Carlo root: {mc_root}")

    return new_column_order


def _infer_production_column(cols: t.Sequence[str]) -> t.Optional[str]:
    prod_col = None
    for c in cols:
        if PRODUCTION_COLUMN_REGEX in c.lower().strip():
            prod_col = c
            break
    return prod_col


def _infer_time_id(df: pd.DataFrame, is_details: bool) -> t.List[int]:
    if is_details:
        return df[TIME_ID_COL].tolist()
    else:
        return list(range(1, len(df) + 1))


class AggregatorManager:
    def __init__(
        self,
        study_path: Path,
        output_id: str,
        query_file: t.Union[MCIndAreasQueryFile, MCAllAreasQueryFile, MCIndLinksQueryFile, MCAllLinksQueryFile],
        frequency: MatrixFrequency,
        ids_to_consider: t.Sequence[str],
        columns_names: t.Sequence[str],
        mc_years: t.Optional[t.Sequence[int]] = None,
    ):
        self.study_path: Path = study_path
        self.output_id: str = output_id
        self.query_file: t.Union[
            MCIndAreasQueryFile, MCAllAreasQueryFile, MCIndLinksQueryFile, MCAllLinksQueryFile
        ] = query_file
        self.frequency: MatrixFrequency = frequency
        self.mc_years: t.Optional[t.Sequence[int]] = mc_years
        self.columns_names: t.Sequence[str] = columns_names
        self.ids_to_consider: t.Sequence[str] = ids_to_consider
        self.output_type = (
            "areas"
            if (isinstance(query_file, MCIndAreasQueryFile) or isinstance(query_file, MCAllAreasQueryFile))
            else "links"
        )
        self.mc_ind_path = self.study_path / MC_TEMPLATE_PARTS.format(
            sim_id=self.output_id, mc_root=MCRoot.MC_IND.value
        )
        self.mc_all_path = self.study_path / MC_TEMPLATE_PARTS.format(
            sim_id=self.output_id, mc_root=MCRoot.MC_ALL.value
        )
        self.mc_root = (
            MCRoot.MC_IND
            if (isinstance(query_file, MCIndAreasQueryFile) or isinstance(query_file, MCIndLinksQueryFile))
            else MCRoot.MC_ALL
        )

    def _parse_output_file(self, file_path: Path, normalize_column_name: bool = True) -> pd.DataFrame:
        csv_file = pd.read_csv(
            file_path,
            sep="\t",
            skiprows=4,
            header=[0, 1, 2],
            na_values="N/A",
            float_precision="legacy",
        )
        date_serializer = FactoryDateSerializer.create(self.frequency.value, "")
        date, body = date_serializer.extract_date(csv_file)
        df = rename_unnamed(body).astype(float)

        df.index = date

        if not normalize_column_name:
            return df

        # normalize columns names
        new_cols = []
        for col in body.columns:
            if self.mc_root == MCRoot.MC_IND:
                name_to_consider = col[0] if self.query_file.value == MCIndAreasQueryFile.VALUES else " ".join(col)
            else:
                name_to_consider = " ".join([col[0], col[2]])
            new_cols.append(name_to_consider.upper().strip())

        df.columns = pd.Index(new_cols)
        return df

    def _filter_ids(self, folder_path: Path) -> t.List[str]:
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

    def _gather_all_files_to_consider__ind(self) -> t.Sequence[Path]:
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
        filtered_files: t.Dict[str, t.MutableSequence[str]] = {}
        for folder_path in folders_to_check:
            for file in folder_path.iterdir():
                if file.stem == f"{self.query_file.value}-{self.frequency}":
                    filtered_files.setdefault(folder_path.name, []).append(file.name)

        # Loop on MC years to return the whole list of files
        all_output_files = [
            self.mc_ind_path / mc_year / self.output_type / area_or_link / file
            for mc_year in all_mc_years
            for area_or_link, files in filtered_files.items()
            for file in files
        ]
        return all_output_files

    def _gather_all_files_to_consider__all(self) -> t.Sequence[Path]:
        # Links / Areas ids filtering
        areas_or_links_ids = self._filter_ids(self.mc_all_path / self.output_type)

        # Frequency and query file filtering
        folders_to_check = [self.mc_all_path / self.output_type / id for id in areas_or_links_ids]
        filtered_files: t.Dict[str, t.MutableSequence[str]] = {}
        for folder_path in folders_to_check:
            for file in folder_path.iterdir():
                if file.stem == f"{self.query_file.value}-{self.frequency}":
                    filtered_files.setdefault(folder_path.name, []).append(file.name)

        # Loop to return the whole list of files
        all_output_files = [
            self.mc_all_path / self.output_type / area_or_link / file
            for area_or_link, files in filtered_files.items()
            for file in files
        ]
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
        if is_details:
            un_normalized_df = self._parse_output_file(file_path, normalize_column_name=False)
            df_len = len(un_normalized_df)
            cluster_dummy_product_cols = sorted(
                set([(x[CLUSTER_ID_COMPONENT], x[DUMMY_COMPONENT]) for x in un_normalized_df.columns])
            )
            actual_cols = sorted(set(un_normalized_df.columns.map(lambda x: x[ACTUAL_COLUMN_COMPONENT])))
            new_obj: t.Dict[str, t.Any] = {k: [] for k in actual_cols}
            new_obj[CLUSTER_ID_COL] = []
            new_obj[TIME_ID_COL] = []
            for cluster_id, dummy_component in cluster_dummy_product_cols:
                for actual_col in actual_cols:
                    col_values = un_normalized_df[(cluster_id, actual_col, dummy_component)].tolist()  # type: ignore
                    new_obj[actual_col] += col_values
                new_obj[CLUSTER_ID_COL] += [cluster_id for _ in range(df_len)]
                new_obj[TIME_ID_COL] += list(range(1, df_len + 1))

            prod_col = _infer_production_column(actual_cols)
            if prod_col is not None:
                new_obj[PRODUCTION_COLUMN_NAME] = new_obj.pop(prod_col)
                actual_cols.remove(prod_col)

            add_prod = [PRODUCTION_COLUMN_NAME] if prod_col is not None else []
            columns_order = [CLUSTER_ID_COL, TIME_ID_COL] + add_prod + list(actual_cols)
            df = pd.DataFrame(new_obj).reindex(columns=columns_order).sort_values(by=[TIME_ID_COL, CLUSTER_ID_COL])
            df.index = pd.Index(list(range(1, len(df) + 1)))

            return df

        else:
            return self._parse_output_file(file_path)

    def _build_dataframe(self, files: t.Sequence[Path], horizon: int) -> pd.DataFrame:
        if self.mc_root not in [MCRoot.MC_IND, MCRoot.MC_ALL]:
            raise InvalidFieldForVersionError(f"Unknown Monte Carlo root: {self.mc_root}")
        is_details = self.query_file in [
            MCIndAreasQueryFile.DETAILS,
            MCAllAreasQueryFile.DETAILS,
            MCIndAreasQueryFile.DETAILS_ST_STORAGE,
            MCAllAreasQueryFile.DETAILS_ST_STORAGE,
            MCIndAreasQueryFile.DETAILS_RES,
            MCAllAreasQueryFile.DETAILS_RES,
        ]
        final_df = pd.DataFrame()
        nb_files = len(files)
        for k, file_path in enumerate(files):
            df = self._process_df(file_path, is_details)

            # columns filtering
            df = self.columns_filtering(df, is_details)

            # if no columns, no need to continue
            list_of_df_columns = df.columns.tolist()
            if not list_of_df_columns or set(list_of_df_columns) == {CLUSTER_ID_COL, TIME_ID_COL}:
                return pd.DataFrame()

            # checks if the estimated dataframe size does not exceed the limit
            # This check is performed on 10 aggregated files to have a more accurate view of the final df.
            if k == 10:
                # The following formula is the more accurate one compared to the final csv file.
                estimated_binary_size = final_df.memory_usage().sum()
                _checks_estimated_size(nb_files, estimated_binary_size, k)

            column_name = AREA_COL if self.output_type == "areas" else LINK_COL
            new_column_order = _columns_ordering(list_of_df_columns, column_name, is_details, self.mc_root)

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
            # add horizon column
            df[TIME_COL] = horizon
            # Reorganize the columns
            df = df.reindex(columns=pd.Index(new_column_order))

            final_df = pd.concat([final_df, df], ignore_index=True)

        # replace np.nan by None
        final_df = final_df.replace({np.nan: None})

        return final_df

    def aggregate_output_data(self) -> pd.DataFrame:
        """
        Aggregates the output data of a study and returns it as a DataFrame
        """

        if self.mc_root == MCRoot.MC_IND:
            # check that the `mc_years` is Sequence[int]
            assert self.mc_years is not None, "mc_years should be a `Sequence` of integers"

            # Checks if mc-ind results exist
            if not self.mc_ind_path.exists():
                raise OutputNotFound(self.output_id)

            # filters files to consider
            all_output_files = sorted(self._gather_all_files_to_consider__ind())

        elif self.mc_root == MCRoot.MC_ALL:
            # Checks if mc-all results exist
            if not self.mc_all_path.exists():
                raise OutputNotFound(self.output_id)

            # filters files to consider
            all_output_files = sorted(self._gather_all_files_to_consider__all())

        else:
            raise InvalidFieldForVersionError(f"Unknown Monte Carlo root: {self.mc_root}")

        # Retrieves the horizon from the study output
        horizon_path = self.study_path / HORIZON_TEMPLATE.format(sim_id=self.output_id)
        launching_config = IniReader().read(horizon_path)
        horizon = launching_config.get("general", {}).get("horizon", 2018)

        logger.info(
            f"Parsing {len(all_output_files)} {self.frequency.value} files"
            f"to build the aggregated output for study `{self.study_path.name}`"
        )
        # builds final dataframe
        final_df = self._build_dataframe(all_output_files, horizon)

        return final_df
