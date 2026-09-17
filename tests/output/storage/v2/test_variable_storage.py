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
from pathlib import Path

import polars as pl
from polars.testing import assert_frame_equal

from antarest.output.filestudy.model import VariableDescription
from antarest.output.storage.v2.metadata import IParquetOutputMetadata
from antarest.output.storage.v2.variables_storage import (
    IndexedOutputDataFrame,
    ParquetOutputWriter,
)


def test_parquet_writer_adapts_df_to_columns(tmp_path: Path) -> None:
    var_cols = [
        VariableDescription("var1", None, "exp"),
        VariableDescription("var2", None, None),
        VariableDescription("var3", None, None),
    ]
    output_df = IndexedOutputDataFrame(
        data=pl.DataFrame(
            [
                pl.Series(name="area", values=["fr", "fr"], dtype=pl.String()),
                pl.Series(name="timeId", values=[1, 2], dtype=pl.Int32()),
                pl.Series(name="1", values=[0, 1], dtype=pl.Float64()),
                pl.Series(name="2", values=[2, 3], dtype=pl.Float64()),
            ]
        ),
        index_cols=["area", "timeId"],
        var_cols=[VariableDescription("var3", None, None), VariableDescription("var1", None, "exp")],
    )
    with ParquetOutputWriter(tmp_path / "output.parquet", ["area", "timeId"], var_cols) as writer:
        writer.append_output_df(output_df)

    adapted_df = pl.read_parquet(tmp_path / "output.parquet")

    # we expect to have second input column in 1st position (var1), then a null column for var2,
    # then 1st input column in 3rd position for var3
    expected_df = pl.DataFrame(
        [
            pl.Series(name="area", values=["fr", "fr"], dtype=pl.String()),
            pl.Series(name="timeId", values=[1, 2], dtype=pl.Int32()),
            pl.Series(name="VAR1 EXP", values=[2, 3], dtype=pl.Float64()),
            pl.Series(name="var2", values=[None, None], dtype=pl.Float64()),
            pl.Series(name="var3", values=[0, 1], dtype=pl.Float64()),
        ]
    )

    assert_frame_equal(adapted_df, expected_df)


def test_area_parquet_file_creation(parquet_dir: Path, parquet_metadata: IParquetOutputMetadata) -> None:
    df = pl.read_parquet(parquet_dir / "mc-ind_areas_monthly.parquet")
    assert df.columns[:3] == ["mcYear", "area", "timeId"]
    assert df.width == 3 + len(parquet_metadata.get_variables("mc-ind", "area"))
    assert df.height == 72
    assert df.filter((pl.col("area") == "fr") & (pl.col("mcYear") == 1))["FR_NUCLEAR"].to_list() == [
        595200.0,
        537600.0,
        595200.0,
        576000.0,
        595200.0,
        576000.0,
        595200.0,
        595200.0,
        576000.0,
        595200.0,
        576000.0,
        576000.0,
    ]
