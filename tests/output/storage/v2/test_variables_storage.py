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
import functools
import os
import uuid
import zipfile
from pathlib import Path

import polars as pl
import pytest

from antarest.output.filestudy.utils import MCIndAreasQueryFile
from antarest.output.model import ClusterVarColumn, OutputTable, VarColumn
from antarest.output.storage.v2.variables_storage import extract_output_to_parquet, read_output_from_parquet
from antarest.study.model import MatrixFrequency


@pytest.fixture(scope="session")
def sta_mini_zip_path(project_path: Path) -> Path:
    return project_path / "examples/studies/STA-mini.zip"


@pytest.fixture(scope="session")
def goodbye_output_path(tmp_path_factory: pytest.TempPathFactory, sta_mini_zip_path: Path) -> Path:
    tmp_dir = tmp_path_factory.mktemp(basename=f"unzipped-output-{uuid.uuid4()}")

    with zipfile.ZipFile(sta_mini_zip_path, "r") as zf:
        zf.extractall(tmp_dir)
    return tmp_dir / "STA-mini" / "output" / "20201014-1425eco-goodbye"


@pytest.fixture(scope="session")
def extra_output_path(tmp_path_factory: pytest.TempPathFactory, sta_mini_zip_path: Path) -> Path:
    tmp_dir = tmp_path_factory.mktemp(basename=f"unzipped-output-{uuid.uuid4()}")

    with zipfile.ZipFile(sta_mini_zip_path, "r") as zf:
        zf.extractall(tmp_dir)
    return tmp_dir / "STA-mini" / "output" / "20241807-1540eco-extra-outputs"


def test_store_variables(goodbye_output_path: Path, tmp_path: Path) -> None:
    parquet_dir = tmp_path / "parquet"
    extract_output_to_parquet(goodbye_output_path, parquet_dir)

    assert sorted(os.listdir(parquet_dir)) == [
        "mc-all_areas_daily.parquet",
        "mc-all_areas_monthly.parquet",
        "mc-all_thermal_clusters_daily.parquet",
        "mc-all_thermal_clusters_monthly.parquet",
        "mc-ind_areas_annual.parquet",
        "mc-ind_areas_hourly.parquet",
        "mc-ind_areas_weekly.parquet",
        "mc-ind_links_hourly.parquet",
        "mc-ind_thermal_clusters_annual.parquet",
        "mc-ind_thermal_clusters_hourly.parquet",
        "mc-ind_thermal_clusters_weekly.parquet",
    ]

    tables = read_output_from_parquet(
        parquet_dir,
        query_file=MCIndAreasQueryFile.VALUES,
        frequency=MatrixFrequency.HOURLY,
        mc_years=[],
        columns_names=[],
        ids_to_consider=[],
    )
    table = functools.reduce(_concat_tables, tables)
    assert table.columns == [
        "area",
        "mcYear",
        "timeId",
        VarColumn(variable="OV. COST", unit="Euro", stat=""),
        VarColumn(variable="OP. COST", unit="Euro", stat=""),
        VarColumn(variable="MRG. PRICE", unit="Euro", stat=""),
        VarColumn(variable="CO2 EMIS.", unit="Tons", stat=""),
        VarColumn(variable="BALANCE", unit="MWh", stat=""),
        VarColumn(variable="ROW BAL.", unit="MWh", stat=""),
        VarColumn(variable="PSP", unit="MWh", stat=""),
        VarColumn(variable="MISC. NDG", unit="MWh", stat=""),
        VarColumn(variable="LOAD", unit="MWh", stat=""),
        VarColumn(variable="H. ROR", unit="MWh", stat=""),
        VarColumn(variable="WIND", unit="MWh", stat=""),
        VarColumn(variable="SOLAR", unit="MWh", stat=""),
        VarColumn(variable="NUCLEAR", unit="MWh", stat=""),
        VarColumn(variable="LIGNITE", unit="MWh", stat=""),
        VarColumn(variable="COAL", unit="MWh", stat=""),
        VarColumn(variable="GAS", unit="MWh", stat=""),
        VarColumn(variable="OIL", unit="MWh", stat=""),
        VarColumn(variable="MIX. FUEL", unit="MWh", stat=""),
        VarColumn(variable="MISC. DTG", unit="MWh", stat=""),
        VarColumn(variable="H. STOR", unit="MWh", stat=""),
        VarColumn(variable="H. PUMP", unit="MWh", stat=""),
        VarColumn(variable="H. LEV", unit="%", stat=""),
        VarColumn(variable="H. INFL", unit="MWh", stat=""),
        VarColumn(variable="H. OVFL", unit="%", stat=""),
        VarColumn(variable="H. VAL", unit="Euro/MWh", stat=""),
        VarColumn(variable="H. COST", unit="Euro", stat=""),
        VarColumn(variable="UNSP. ENRG", unit="MWh", stat=""),
        VarColumn(variable="SPIL. ENRG", unit="MWh", stat=""),
        VarColumn(variable="LOLD", unit="Hours", stat=""),
        VarColumn(variable="LOLP", unit="%", stat=""),
        VarColumn(variable="AVL DTG", unit="MWh", stat=""),
        VarColumn(variable="DTG MRG", unit="MWh", stat=""),
        VarColumn(variable="MAX MRG", unit="MWh", stat=""),
        VarColumn(variable="NP COST", unit="Euro", stat=""),
        VarColumn(variable="NODU", unit="", stat=""),
    ]

    tables = read_output_from_parquet(
        parquet_dir,
        query_file=MCIndAreasQueryFile.DETAILS,
        frequency=MatrixFrequency.HOURLY,
        mc_years=[1],
        columns_names=[],
        ids_to_consider=["de", "fr", "it"],
    )
    table = functools.reduce(_concat_tables, tables, OutputTable(data=pl.DataFrame([]), columns=[]))

    assert table.columns == [
        "area",
        "cluster",
        "mcYear",
        "timeId",
        ClusterVarColumn(variable="MWh", stat=""),
        ClusterVarColumn(variable="NODU", stat=""),
        ClusterVarColumn(variable="NP Cost - Euro", stat=""),
    ]


def _concat_tables(left: OutputTable, right: OutputTable) -> OutputTable:
    if not left.columns:
        return right
    if left.columns != right.columns:
        raise ValueError("Output columns mismatch.")

    return OutputTable(
        data=pl.concat([left.data, right.data], how="vertical"),
        columns=right.columns,
    )


def test_store_variables_extra(extra_output_path: Path, tmp_path: Path) -> None:
    parquet_dir = tmp_path / "parquet"
    extract_output_to_parquet(extra_output_path, parquet_dir)

    assert sorted(os.listdir(parquet_dir)) == [
        "mc-all_binding_constraints_annual.parquet",
        "mc-all_binding_constraints_monthly.parquet",
        "mc-all_districts_annual.parquet",
        "mc-all_districts_monthly.parquet",
        "mc-all_links_annual.parquet",
        "mc-all_links_daily.parquet",
        "mc-all_links_hourly.parquet",
        "mc-all_links_monthly.parquet",
        "mc-all_links_weekly.parquet",
        "mc-ind_binding_constraints_daily.parquet",
        "mc-ind_binding_constraints_hourly.parquet",
        "mc-ind_districts_annual.parquet",
        "mc-ind_links_annual.parquet",
        "mc-ind_links_daily.parquet",
        "mc-ind_links_hourly.parquet",
        "mc-ind_links_monthly.parquet",
        "mc-ind_links_weekly.parquet",
    ]
