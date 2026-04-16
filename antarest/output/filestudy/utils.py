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
from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum, StrEnum
from io import StringIO
from itertools import islice
from pathlib import Path
from typing import IO, TypeAlias

import pandas as pd
import polars as pl
from polars.exceptions import ComputeError

from antarest.output.model import OutputTable, VarColumn
from antarest.study.model import MatrixFrequency, MatrixIndex, TimeSerie

"""Column name for the Monte Carlo year."""
MCYEAR_COL = "mcYear"

RAW_OUTPUT_MATRIX_METADATA_COLUMNS = ("area", "link", "timeId", "mcYear", "cluster")
RAW_OUTPUT_MATRIX_HEADER_SEPARATOR = " % "

"""Column name for the time index."""
TIME_ID_COL = "timeId"


class MCRoot(Enum):
    MC_IND = "mc-ind"
    MC_ALL = "mc-all"


class MCIndAreasQueryFile(StrEnum):
    VALUES = "values"
    DETAILS = "details"
    DETAILS_ST_STORAGE = "details-STstorage"
    DETAILS_RES = "details-res"


class MCAllAreasQueryFile(StrEnum):
    VALUES = "values"
    DETAILS = "details"
    DETAILS_ST_STORAGE = "details-STstorage"
    DETAILS_RES = "details-res"
    ID = "id"


class MCIndLinksQueryFile(StrEnum):
    VALUES = "values"


class MCAllLinksQueryFile(StrEnum):
    VALUES = "values"
    ID = "id"


class MCIndBCQueryFile(StrEnum):
    BINDING_CONSTRAINTS = "binding-constraints"


class MCAllBCQueryFile(StrEnum):
    BINDING_CONSTRAINTS = "binding-constraints"


QueryFileType: TypeAlias = (
    MCIndAreasQueryFile
    | MCAllAreasQueryFile
    | MCIndLinksQueryFile
    | MCAllLinksQueryFile
    | MCIndBCQueryFile
    | MCAllBCQueryFile
)


@dataclass(frozen=True)
class RawOutputMatrixQuery:
    """Parsed parameters from the /raw output matrix path"""

    output_id: str
    query_file: QueryFileType
    frequency: MatrixFrequency
    ids_to_consider: str
    mc_year: int | None


_QUERY_FILE_MAP: dict[tuple[str, str], dict[str, QueryFileType]] = {
    ("mc-all", "areas"): {e.value: e for e in MCAllAreasQueryFile},
    ("mc-all", "links"): {e.value: e for e in MCAllLinksQueryFile},
    ("mc-ind", "areas"): {e.value: e for e in MCIndAreasQueryFile},
    ("mc-ind", "links"): {e.value: e for e in MCIndLinksQueryFile},
}


def parse_raw_output_matrix_path(path_parts: list[str]) -> RawOutputMatrixQuery | None:
    """
    Parses a legacy /raw path targeting an output matrix into aggregation parameters.

    Expected path structures:
        output/{output_id}/{mode}/mc-all/{areas_or_links}/{id}/{query_file}-{frequency}
        output/{output_id}/{mode}/mc-all/links/{upstream}/{downstream}/{query_file}-{frequency}
        output/{output_id}/{mode}/mc-ind/{mc_year}/{areas_or_links}/{id}/{query_file}-{frequency}
        output/{output_id}/{mode}/mc-ind/{mc_year}/links/{upstream}/{downstream}/{query_file}-{frequency}

    Returns None if the path does not match an output matrix pattern.
    """
    if len(path_parts) < 7 or path_parts[0] != "output":
        return None

    mc_root = path_parts[3]

    if mc_root == "mc-ind":
        if len(path_parts) < 8:
            return None
        try:
            mc_year = int(path_parts[4])
        except ValueError:
            return None
        area_or_link = path_parts[5]
        path_offset = 6
    elif mc_root == "mc-all":
        area_or_link = path_parts[4]
        path_offset = 5
        mc_year = None
    else:
        return None

    if area_or_link == "areas":
        if len(path_parts) != path_offset + 2:
            return None
        item_id = path_parts[path_offset]
        file_segment = path_parts[path_offset + 1]
    elif area_or_link == "links":
        if len(path_parts) != path_offset + 3:
            return None
        item_id = f"{path_parts[path_offset]} - {path_parts[path_offset + 1]}"
        file_segment = path_parts[path_offset + 2]
    else:
        return None

    query_file_options = _QUERY_FILE_MAP.get((mc_root, area_or_link))
    if query_file_options is None:
        return None

    frequency = None
    query_file = None
    for freq in MatrixFrequency:
        suffix = f"-{freq.value}"
        if file_segment.endswith(suffix):
            candidate = query_file_options.get(file_segment[: -len(suffix)])
            if candidate is not None:
                frequency = freq
                query_file = candidate
                break

    if frequency is None or query_file is None:
        return None

    return RawOutputMatrixQuery(
        output_id=path_parts[1],
        query_file=query_file,
        frequency=frequency,
        ids_to_consider=item_id,
        mc_year=mc_year,
    )


def get_output_object_type(file_type: QueryFileType, is_link: bool) -> str:
    if is_link:
        return "links"

    match file_type:
        case MCIndAreasQueryFile.DETAILS:
            return "thermal_clusters"
        case MCIndAreasQueryFile.DETAILS_RES:
            return "renewable_clusters"
        case MCIndAreasQueryFile.DETAILS_ST_STORAGE:
            return "short_term_storages"
        case _:
            return "areas"


def get_start_column(frequency: MatrixFrequency) -> int:
    if frequency == MatrixFrequency.ANNUAL:
        return 2
    elif frequency == MatrixFrequency.MONTHLY:
        return 3
    elif frequency == MatrixFrequency.WEEKLY:
        return 2
    elif frequency == MatrixFrequency.DAILY:
        return 4
    elif frequency == MatrixFrequency.HOURLY:
        return 5
    else:
        raise NotImplementedError(f"Unknown frequency {frequency.value}")


def parse_headers(content: IO[str], start_col: int) -> list[VarColumn]:
    header_lines: list[list[str]] = []
    for line in islice(content, 4, 7):  # Note: avoids to go over the whole file, much faster for larger files
        cols = [s.strip() for s in line.split("\t")[start_col:]]
        if not header_lines:
            header_lines = [[col] for col in cols]
        else:
            for k, col in enumerate(cols):
                header_lines[k].append(col)
    return [
        VarColumn(variable=col[0], unit=col[1] if len(col) > 1 else "", stat=col[2] if len(col) > 2 else "")
        for col in header_lines
    ]


def split_concatenated_columns_from_dataframe(df: pd.DataFrame) -> Iterator[TimeSerie]:
    """
    Performs the inverse transformation compared to the concatenate method. Also used inside Imagrid endpoint.
    """
    for column in df.columns:
        splitted_col = column.split(" % ")
        name, unit = splitted_col[0], splitted_col[1]
        yield TimeSerie(name=name, unit=unit or " ", data=df[column].to_numpy())


def add_time_index_to_dataframe(df: pd.DataFrame, matrix_index: MatrixIndex) -> None:
    time_column = pd.date_range(start=matrix_index.start_date, periods=len(df), freq=matrix_index.level.value[0])
    df.index = time_column


def _parse_output_dataframe(content: str) -> pl.DataFrame:
    try:
        return pl.read_csv(
            StringIO(content), skip_lines=7, separator="\t", has_header=False, null_values="N/A", n_threads=1
        )
    except ComputeError:
        # Happens if polars wrongly inferred the schema.
        # If so, we specify that it should read the entire file to be sure it doesn't infer a false schema.
        # It's significantly slower but it does not fail.
        # As no file is longer than 10.000 rows we use this value.
        return pl.read_csv(
            StringIO(content),
            skip_lines=7,
            separator="\t",
            has_header=False,
            null_values="N/A",
            infer_schema_length=10000,
            n_threads=1,
        )


def parse_output_file(file_path: Path, first_column: int) -> OutputTable:
    content = file_path.read_text(encoding="utf-8")
    output_headers = parse_headers(StringIO(content), first_column)
    polars_df = _parse_output_dataframe(content)

    df = polars_df[polars_df.columns[first_column:]]

    # At this point we only have numeric values in our df. But NaN columns are considered to be String by polars.
    # So we change this to be Float64 to harmonize everything.
    df = df.with_columns(pl.col(pl.Utf8).cast(pl.Float64))

    return OutputTable(data=df, columns=output_headers)
