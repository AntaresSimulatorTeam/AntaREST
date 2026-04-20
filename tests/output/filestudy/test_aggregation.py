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
import zipfile
from pathlib import Path

import polars as pl
import pytest
from polars.testing import assert_frame_equal

from antarest.output.filestudy.aggregation import (
    OutputFile,
    OutputMatrix,
    filter_columns,
    identify_files,
    sort_columns,
    stack_matrix,
)
from antarest.output.model import ClusterVarColumn, LazyOutputTable, MCAllAreasData, MCIndAreasData, VarColumn
from antarest.study.model import MatrixFrequency
from tests.test_helpers.matchers import ends_with


@pytest.fixture
def sta_mini_zip_path(project_path: Path) -> Path:
    return project_path / "examples/studies/STA-mini.zip"


def _extract_output(tmp_path: Path, sta_mini_zip_path: Path, output_name: str) -> Path:
    target = tmp_path / "STA-mini"
    with zipfile.ZipFile(sta_mini_zip_path, "r") as zf:
        zf.extractall(target, members=[m for m in zf.infolist() if output_name in m.filename])
    return target / "STA-mini" / "output" / output_name


@pytest.fixture
def output_path(tmp_path: Path, sta_mini_zip_path: Path) -> Path:
    return _extract_output(tmp_path, sta_mini_zip_path, "20201014-1427eco")


@pytest.fixture
def mc_ind_output_path(tmp_path: Path, sta_mini_zip_path: Path) -> Path:
    return _extract_output(tmp_path, sta_mini_zip_path, "20201014-1422eco-hello")


def test_identify_mc_all_files(output_path: Path) -> None:
    files = identify_files(output_path, MCAllAreasData.VALUES, MatrixFrequency.DAILY, [])
    assert files == [
        OutputFile(path=ends_with("values-daily.txt"), year=None, location="de"),
        OutputFile(path=ends_with("values-daily.txt"), year=None, location="es"),
    ]
    assert identify_files(output_path, MCAllAreasData.VALUES, MatrixFrequency.DAILY, ["es"]) == [
        OutputFile(path=ends_with("values-daily.txt"), year=None, location="es"),
    ]

    assert identify_files(output_path, MCAllAreasData.VALUES, MatrixFrequency.HOURLY, []) == []

    assert identify_files(output_path, MCAllAreasData.DETAILS, MatrixFrequency.DAILY, []) == [
        OutputFile(path=ends_with("details-daily.txt"), year=None, location="de"),
        OutputFile(path=ends_with("details-daily.txt"), year=None, location="es"),
    ]


def test_identify_mc_ind_files(mc_ind_output_path: Path) -> None:
    output_path = mc_ind_output_path
    files = identify_files(output_path, MCIndAreasData.VALUES, MatrixFrequency.DAILY, [])
    assert files == []

    assert identify_files(output_path, MCIndAreasData.VALUES, MatrixFrequency.HOURLY, []) == [
        OutputFile(
            path=ends_with("values-hourly.txt"),
            year=1,
            location="de",
        ),
        OutputFile(
            path=ends_with("values-hourly.txt"),
            year=1,
            location="es",
        ),
        OutputFile(
            path=ends_with("values-hourly.txt"),
            year=1,
            location="fr",
        ),
        OutputFile(
            path=ends_with("values-hourly.txt"),
            year=1,
            location="it",
        ),
    ]

    assert identify_files(output_path, MCIndAreasData.VALUES, MatrixFrequency.HOURLY, ["es"]) == [
        OutputFile(path=ends_with("values-hourly.txt"), year=1, location="es")
    ]

    assert identify_files(output_path, MCIndAreasData.VALUES, MatrixFrequency.HOURLY, ["es"], mc_years=[1]) == [
        OutputFile(path=ends_with("values-hourly.txt"), year=1, location="es")
    ]
    assert identify_files(output_path, MCIndAreasData.VALUES, MatrixFrequency.HOURLY, ["es"], mc_years=[2]) == []


def test_filter_columns__no_filter_should_keep_all_columns() -> None:
    df = pl.DataFrame(
        data={
            "1": [0, 1, 2],
            "2": [10, 11, 12],
            "3": [20, 21, 22],
        }
    )
    cols = [VarColumn("VAR1", "MWh", None), VarColumn("VAR2", "MWh", None), VarColumn("VAR3", "MWh", None)]
    table = LazyOutputTable(columns=cols, dataframe=df)
    output_matrix = OutputMatrix(
        path=Path("/test/path"), file_type=MCAllAreasData.VALUES, data=table, location="my-area", year=10
    )

    filtered = filter_columns(output_matrix, [])
    assert filtered.path == output_matrix.path
    assert filtered.year == output_matrix.year
    assert filtered.location == output_matrix.location
    assert filtered.data.columns == output_matrix.data.columns
    assert_frame_equal(output_matrix.data.dataframe, filtered.data.dataframe)


def test_filter_columns__with_filters() -> None:
    df = pl.DataFrame(
        data={
            "1": [0, 1, 2],
            "2": [10, 11, 12],
            "3": [20, 21, 22],
        }
    )
    cols = [VarColumn("VAR1", "MWh", None), VarColumn("VAR2", "MWh", None), VarColumn("VAR3", "MWh", None)]
    table = LazyOutputTable(columns=cols, dataframe=df.lazy())
    output_matrix = OutputMatrix(
        path=Path("/test/path"), file_type=MCAllAreasData.VALUES, data=table, location="my-area", year=10
    )

    filtered = filter_columns(output_matrix, ["VAR3", "Var1"])
    assert filtered.path == output_matrix.path
    assert filtered.file_type == output_matrix.file_type
    assert filtered.year == output_matrix.year
    assert filtered.data.columns == [
        VarColumn("VAR1", "MWh", None),
        VarColumn("VAR3", "MWh", None),
    ]
    expected_df = pl.DataFrame(
        data={
            "1": [0, 1, 2],
            "3": [20, 21, 22],
        }
    )
    assert_frame_equal(filtered.data.dataframe.collect(), expected_df)


def test_filter_columns__with_clusters_vars() -> None:

    df = pl.DataFrame(
        data={
            "1": ["c1", "c1", "c2"],
            "2": [0, 1, 2],
            "3": [10, 11, 12],
            "4": [20, 21, 22],
        }
    )
    cols = [
        "clusterId",
        ClusterVarColumn("MWh", None),
        ClusterVarColumn("Euro", None),
        ClusterVarColumn("%", None),
    ]
    table = LazyOutputTable(columns=cols, dataframe=df.lazy())
    output_matrix = OutputMatrix(
        path=Path("/test/path"), file_type=MCAllAreasData.VALUES, data=table, location="my-area", year=10
    )

    filtered = filter_columns(output_matrix, ["euro", "%"])
    assert filtered.path == output_matrix.path
    assert filtered.year == output_matrix.year
    assert filtered.file_type == output_matrix.file_type
    assert filtered.data.columns == [
        "clusterId",
        ClusterVarColumn("Euro", None),
        ClusterVarColumn("%", None),
    ]
    expected_df = pl.DataFrame(
        data={
            "1": ["c1", "c1", "c2"],
            "3": [10, 11, 12],
            "4": [20, 21, 22],
        }
    )
    assert_frame_equal(filtered.data.dataframe.collect(), expected_df)


def test_stack_matrix() -> None:
    df = pl.DataFrame(
        data={
            "timeId": [0, 1, 2],
            "1": [0, 1, 2],  # cluster 1 var1
            "2": [10, 11, 12],  # cluster 2 var1
            "3": [20, 21, 22],  # cluster 3 var1
            "4": [30, 31, 32],  # cluster 2 var2
            "5": [40, 41, 42],  # cluster 1 var2
            "6": [50, 51, 52],  # cluster 3 var2
        }
    )
    cols = [
        "timeId",
        VarColumn("cluster1", "var1", None),
        VarColumn("cluster2", "var1", None),
        VarColumn("cluster3", "var1", None),
        VarColumn("cluster2", "var2", None),
        VarColumn("cluster1", "var2", None),
        VarColumn("cluster3", "var2", None),
    ]
    table = LazyOutputTable(columns=cols, dataframe=df.lazy())
    output_matrix = OutputMatrix(
        path=Path("/test/path"), file_type=MCAllAreasData.VALUES, data=table, location="my-area", year=10
    )
    stacked = stack_matrix(output_matrix)

    assert stacked.path == output_matrix.path
    assert stacked.year == output_matrix.year
    assert stacked.data.columns == ["cluster", "timeId", ClusterVarColumn("var1", None), ClusterVarColumn("var2", None)]

    # 3 columns now: 1 for cluster IDs, one for var1, one for var2
    expected_df = pl.DataFrame(
        data={
            "cluster": [
                "cluster1",
                "cluster1",
                "cluster1",
                "cluster2",
                "cluster2",
                "cluster2",
                "cluster3",
                "cluster3",
                "cluster3",
            ],
            "timeId": [0, 1, 2, 0, 1, 2, 0, 1, 2],
            "0": [0, 1, 2, 10, 11, 12, 20, 21, 22],
            "1": [40, 41, 42, 30, 31, 32, 50, 51, 52],
        }
    )

    stacked_df = stacked.data.dataframe.collect()
    assert_frame_equal(stacked_df, expected_df)


def test_sort_columns() -> None:
    unsorted_df = pl.DataFrame(
        data={
            "cluster": ["cluster"],
            "timeId": [0],
            "area": ["fr"],
            "mcYear": [20],
            "0": [30],
            "1": [40],
        }
    )
    unsorted_cols = [
        "cluster",
        "timeId",
        "area",
        "mcYear",
        VarColumn("v2", "MWh", None),
        VarColumn("v1", "MWh", None),
    ]
    table = LazyOutputTable(columns=unsorted_cols, dataframe=unsorted_df.lazy())
    unsorted = OutputMatrix(
        path=Path("/test/path"), file_type=MCAllAreasData.VALUES, data=table, location="my-area", year=10
    )

    sorted = sort_columns(unsorted)

    assert sorted.data.columns == [
        "area",
        "cluster",
        "mcYear",
        "timeId",
        VarColumn("v2", "MWh", None),
        VarColumn("v1", "MWh", None),
    ]
    expected_df = pl.DataFrame(
        data={
            "area": ["fr"],
            "cluster": ["cluster"],
            "mcYear": [20],
            "timeId": [0],
            "0": [30],
            "1": [40],
        }
    )
    assert_frame_equal(sorted.data.dataframe.collect(), expected_df)
