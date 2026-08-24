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
import pytest
from polars.testing import assert_frame_equal
from sqlalchemy.orm import Session

from antarest.output.filestudy.model import FileOutput, VariableDescription
from antarest.output.storage.v2.dbmodel import DbParquetOutput
from antarest.output.storage.v2.variables_fetching import get_variables_index
from antarest.output.storage.v2.variables_parsing import extract_output_variables_to_database
from antarest.output.storage.v2.variables_storage import (
    IndexedOutputDataFrame,
    ParquetOutputWriter,
    extract_areas_refacto,
)


@pytest.fixture
def output_dir(data_dir: Path) -> Path:
    return data_dir / "20260810-1420eco-thermal_groups"


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
            pl.Series(name="var1__exp", values=[2, 3], dtype=pl.Float64()),
            pl.Series(name="var2", values=[None, None], dtype=pl.Float64()),
            pl.Series(name="var3", values=[0, 1], dtype=pl.Float64()),
        ]
    )

    assert_frame_equal(adapted_df, expected_df)


def test_area_parquet_file_creation(output_dir: Path, db_session: Session, tmp_path: Path) -> None:
    # TODO: should probably not need to go to the DB to get variables index ...
    # TODO: should not get any file for empty frequencies

    db_output = DbParquetOutput(id=0)
    db_session.add(db_output)
    db_session.flush()

    file_output = FileOutput(output_dir)
    extract_output_variables_to_database(db_session, db_output.id, file_output)
    db_session.flush()

    extract_output_variables_to_database(db_session, 0, file_output)
    index = get_variables_index(db_session, 0)

    target_dir = tmp_path / "output"
    target_dir.mkdir()

    extract_areas_refacto(index, file_output, target_dir)

    monthly_file = target_dir / "mc-ind_areas_monthly.parquet"
    assert monthly_file.is_file()

    df = pl.read_parquet(monthly_file)

    assert df.columns == [
        "mcYear",
        "area",
        "timeId",
        "CO2 EMIS.__MWh",
        "AVL DTG__MWh",
        "DTG MRG__MWh",
        "MAX MRG__MWh",
        "NP COST__Euro",
        "RES LOAD__MWh",
        "NODU",
        "ES_NUCLEAR_TH_PROD__MWh",
        "FR_NUCLEAR_TH_PROD__MWh",
        "CO2 EMIS.__Tons",
        "ES_NUCLEAR__MWh",
        "FR_NUCLEAR__MWh",
    ]
