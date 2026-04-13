import zipfile
from pathlib import Path

import plyer.platforms.macosx.libs.osx_motion_sensor
import polars as pl
import pytest
from polars.testing import assert_frame_equal

from antarest.output.filestudy.aggregator_management import (
    AggregatorManager,
    OutputMatrix,
    add_index_columns,
    filter_columns,
    sort_columns,
    stack_matrix,
)
from antarest.output.filestudy.utils import MCAllAreasQueryFile, parse_output_file
from antarest.output.model import ClusterVarColumn, VarColumn
from antarest.study.model import MatrixFrequency


@pytest.fixture
def sta_mini_zip_path(project_path: Path) -> Path:
    return project_path / "examples/studies/STA-mini.zip"


@pytest.fixture
def output_path(tmp_path: Path, sta_mini_zip_path: Path) -> Path:
    target = tmp_path / "STA-mini"
    with zipfile.ZipFile(sta_mini_zip_path, "r") as zf:
        zf.extractall(target)
    return target / "STA-mini" / "output" / "20201014-1427eco"


def test_aggregation(output_path: Path) -> None:
    dfs = AggregatorManager(
        output_path, MCAllAreasQueryFile.VALUES, MatrixFrequency.DAILY, [], [], False, []
    ).aggregate_output_data()
    dfs = list(dfs)
    assert dfs[0].columns == []


def test_identify_files() -> None:
    pass


def test_iterate_dataframes() -> None:
    pass


def test_filter_columns__no_filter_should_keep_all_columns() -> None:
    df = pl.DataFrame(
        data={
            "1": [0, 1, 2],
            "2": [10, 11, 12],
            "3": [20, 21, 22],
        }
    )
    cols = [VarColumn("VAR1", "MWh", None), VarColumn("VAR2", "MWh", None), VarColumn("VAR3", "MWh", None)]
    output_matrix = OutputMatrix(columns=cols, data=df.lazy(), location="my-area", path=Path("/test/path"), year=10)

    filtered = filter_columns(output_matrix, [])
    assert filtered.columns == output_matrix.columns
    assert_frame_equal(output_matrix.data, filtered.data)
    assert filtered.columns == output_matrix.columns
    assert filtered.path == output_matrix.path
    assert filtered.year == output_matrix.year


def test_filter_columns__with_filters() -> None:
    df = pl.DataFrame(
        data={
            "1": [0, 1, 2],
            "2": [10, 11, 12],
            "3": [20, 21, 22],
        }
    )
    cols = [VarColumn("VAR1", "MWh", None), VarColumn("VAR2", "MWh", None), VarColumn("VAR3", "MWh", None)]
    output_matrix = OutputMatrix(columns=cols, data=df.lazy(), location="my-area", path=Path("/test/path"), year=10)

    filtered = filter_columns(output_matrix, ["VAR3", "Var1"])
    assert filtered.columns == [
        VarColumn("VAR1", "MWh", None),
        VarColumn("VAR3", "MWh", None),
    ]
    expected_df = pl.DataFrame(
        data={
            "1": [0, 1, 2],
            "3": [20, 21, 22],
        }
    )
    assert_frame_equal(filtered.data.collect(), expected_df)
    assert filtered.path == output_matrix.path
    assert filtered.year == output_matrix.year


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
    output_matrix = OutputMatrix(columns=cols, data=df.lazy(), location="my-area", path=Path("/test/path"), year=10)

    filtered = filter_columns(output_matrix, ["euro", "%"])
    assert filtered.columns == [
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
    assert_frame_equal(filtered.data.collect(), expected_df)
    assert filtered.path == output_matrix.path
    assert filtered.year == output_matrix.year


def test_unpivot_matrix() -> None:
    df = pl.DataFrame(
        data={
            "time": [0, 1, 2],
            "1": [0, 1, 2],  # cluster 1 var1
            "2": [10, 11, 12],  # cluster 2 var1
            "3": [20, 21, 22],  # cluster 3 var1
            "4": [30, 31, 32],  # cluster 2 var2
            "5": [40, 41, 42],  # cluster 1 var2
            "6": [50, 51, 52],  # cluster 3 var2
        }
    )
    cols = [
        "time",
        VarColumn("cluster1", "var1", None),
        VarColumn("cluster2", "var1", None),
        VarColumn("cluster3", "var1", None),
        VarColumn("cluster2", "var2", None),
        VarColumn("cluster1", "var2", None),
        VarColumn("cluster3", "var2", None),
    ]

    output_matrix = OutputMatrix(columns=cols, data=df.lazy(), location="my-area", path=Path("/test/path"), year=10)
    stacked = stack_matrix(output_matrix)

    assert stacked.path == output_matrix.path
    assert stacked.year == output_matrix.year
    assert stacked.columns == ["cluster", "time", ClusterVarColumn("var1", None), ClusterVarColumn("var2", None)]

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
            "time": [0, 1, 2, 0, 1, 2, 0, 1, 2],
            "0": [0, 1, 2, 10, 11, 12, 20, 21, 22],
            "1": [40, 41, 42, 30, 31, 32, 50, 51, 52],
        }
    )

    stacked_df = stacked.data.collect()
    assert_frame_equal(stacked_df, expected_df)


# TODO: a supprimer
@pytest.fixture
def output_matrix() -> OutputMatrix:
    path = Path(
        "/home/leclercsyl/feature_tests/antares/output-agregation/output/20250127-1459eco/economy/mc-ind/00001/areas/fr/details-hourly.txt"
    )
    matrix = parse_output_file(path, 5)
    return OutputMatrix(data=matrix.data.lazy(), columns=matrix.headers, year=1, path=path, location="my-area")


def test_with_real_data(output_matrix: OutputMatrix) -> None:

    with_index = add_index_columns(output_matrix)
    with_index.data.collect()
    stacked = stack_matrix(with_index)
    stacked.data.collect()


def test_sort_columns() -> None:
    unsorted_df = pl.DataFrame(
        data={
            "cluster": ["cluster"],
            "time": [0],
            "location": ["fr"],
            "year": [20],
            "0": [30],
            "1": [40],
        }
    )
    unsorted_cols = ["cluster", "time", "location", "year", VarColumn("v2", "MWh", None), VarColumn("v1", "MWh", None)]
    unsorted = OutputMatrix(
        columns=unsorted_cols, data=unsorted_df.lazy(), location="my-area", path=Path("/test/path"), year=10
    )

    sorted = sort_columns(unsorted)

    assert sorted.columns == [
        "location",
        "cluster",
        "year",
        "time",
        VarColumn("v2", "MWh", None),
        VarColumn("v1", "MWh", None),
    ]
    expected_df = pl.DataFrame(
        data={
            "location": ["fr"],
            "cluster": ["cluster"],
            "year": [20],
            "time": [0],
            "0": [30],
            "1": [40],
        }
    )
    assert_frame_equal(sorted.data.collect(), expected_df)
