import logging
import typing as t
from enum import Enum
from pathlib import Path

import numpy as np
import pandas as pd

from antarest.core.exceptions import FileTooLargeError, OutputNotFound
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
MC_YEAR_INDEX = 0
"""Index in path parts starting from the Monte Carlo year to determine the Monte Carlo year."""
AREA_OR_LINK_INDEX__IND, AREA_OR_LINK_INDEX__ALL = 2, 1
"""Indexes in path parts starting from the output root `economy//mc-(ind/all)` to determine the area/link name."""

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

    def _parse_output_file(self, file_path: Path) -> pd.DataFrame:
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

        # normalize columns names
        new_cols = []
        for col in body.columns:
            name_to_consider = col[0] if self.query_file.value == MCIndAreasQueryFile.VALUES else " ".join(col)
            new_cols.append(name_to_consider.upper().strip())

        df.index = date
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
                filtered_columns = [
                    c for c in df.columns.tolist() if any(regex in c.lower() for regex in lower_case_columns)
                ]
            else:
                filtered_columns = [c for c in df.columns.tolist() if c.lower() in lower_case_columns]
            df = df.loc[:, filtered_columns]
        return df

    def _build_dataframe(self, files: t.Sequence[Path], horizon: int) -> pd.DataFrame:
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
            df = self._parse_output_file(file_path)

            # columns filtering
            df = self.columns_filtering(df, is_details)

            # if no columns, no need to continue
            list_of_df_columns = df.columns.tolist()
            if not list_of_df_columns:
                return pd.DataFrame()

            # checks if the estimated dataframe size does not exceed the limit
            # This check is performed on 10 aggregated files to have a more accurate view of the final df.
            if k == 10:
                # The following formula is the more accurate one compared to the final csv file.
                estimated_binary_size = final_df.memory_usage().sum()
                _checks_estimated_size(nb_files, estimated_binary_size, k)

            if self.mc_root == MCRoot.MC_IND:
                # add column for links/areas
                relative_path_parts = file_path.relative_to(self.mc_ind_path).parts
                column_name = AREA_COL if self.output_type == "areas" else LINK_COL
                new_column_order = [column_name, MCYEAR_COL, TIME_ID_COL, TIME_COL] + list_of_df_columns
                df[column_name] = relative_path_parts[AREA_OR_LINK_INDEX__IND]

                # add column to record the Monte Carlo year
                df[MCYEAR_COL] = int(relative_path_parts[MC_YEAR_INDEX])

                # add a column for the time id
                df[TIME_ID_COL] = list(range(1, len(df) + 1))
                # add horizon column
                df[TIME_COL] = horizon

                # Reorganize the columns
                df = df.reindex(columns=new_column_order)
            else:
                # first columns df
                # first we include the time id column
                first_columns_df = pd.DataFrame(
                    {
                        TIME_ID_COL: list(range(1, len(df) + 1)),
                    }
                )

                # add column for links/areas
                relative_path_parts = file_path.relative_to(self.mc_all_path).parts
                column_name = AREA_COL if self.output_type == "areas" else LINK_COL
                first_columns_df[column_name] = relative_path_parts[AREA_OR_LINK_INDEX__ALL]

                # add horizon column
                first_columns_df[TIME_COL] = horizon

                # reorder first columns
                new_column_order = [column_name, TIME_ID_COL, TIME_COL]
                first_columns_df = first_columns_df.reindex(columns=new_column_order)

                # reset index
                # noinspection PyTypeChecker
                first_columns_df.set_index(df.index, inplace=True)

                # merge first columns with the rest of the df
                df = pd.merge(first_columns_df, df, left_index=True, right_index=True)

            final_df = pd.concat([final_df, df], ignore_index=True)

        # replace np.nan by None
        final_df = final_df.replace({np.nan: None})

        return final_df

    def aggregate_output_data(self) -> pd.DataFrame:
        """
        Aggregates the output data of a study and returns it as a DataFrame
        """

        # check that the `mc_years` is Sequence[int]
        assert self.mc_years is not None, "mc_years should be a `Sequence` of integers"

        # Checks if mc-ind results exist
        if not self.mc_ind_path.exists():
            raise OutputNotFound(self.output_id)

        # Retrieves the horizon from the study output
        horizon_path = self.study_path / HORIZON_TEMPLATE.format(sim_id=self.output_id)
        launching_config = IniReader().read(horizon_path)
        horizon = launching_config.get("general", {}).get("horizon", 2018)

        # filters files to consider
        all_output_files = sorted(self._gather_all_files_to_consider__ind())

        logger.info(
            f"Parsing {len(all_output_files)} {self.frequency.value} files"
            f"to build the aggregated output for study `{self.study_path.name}`"
        )
        # builds final dataframe
        final_df = self._build_dataframe(all_output_files, horizon)

        return final_df

    def aggregate_output_data__all(self) -> pd.DataFrame:
        """
        Aggregates the output data of a study and returns it as a DataFrame
        """

        # Checks if mc-all results exist
        if not self.mc_all_path.exists():
            raise OutputNotFound(self.output_id)

        # Retrieves the horizon from the study output
        horizon_path = self.study_path / HORIZON_TEMPLATE.format(sim_id=self.output_id)
        launching_config = IniReader().read(horizon_path)
        horizon = launching_config.get("general", {}).get("horizon", 2018)

        # filters files to consider
        all_output_files = sorted(self._gather_all_files_to_consider__all())

        logger.info(
            f"Parsing {len(all_output_files)} {self.frequency.value} files"
            f"to build the aggregated output for study `{self.study_path.name}`"
        )
        # builds final dataframe
        final_df = self._build_dataframe(all_output_files, horizon)

        return final_df
