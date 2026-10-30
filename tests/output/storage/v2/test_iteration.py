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

from antarest.output.filestudy.model import VariableDescription
from antarest.output.storage.v2.iteration import iterate_areas_df
from antarest.output.storage.v2.metadata import IParquetOutputMetadata
from antarest.study.model import MatrixFrequency


def test_iterate_areas(parquet_dir: Path, parquet_metadata: IParquetOutputMetadata) -> None:

    area_dfs = list(iterate_areas_df(parquet_metadata, parquet_dir, MatrixFrequency.MONTHLY, [], [], []))

    assert len(area_dfs) == 6  # 2 years, 3 "areas" (1 district ...)

    assert [(a.year, a.area_id) for a in area_dfs] == [
        (1, "@ all areas"),
        (1, "es"),
        (1, "fr"),
        (2, "@ all areas"),
        (2, "es"),
        (2, "fr"),
    ]

    # Check district variables
    assert area_dfs[0].variables == [
        VariableDescription(name="CO2 EMIS.", unit="MWh", statistic_type=None),
        VariableDescription(name="AVL DTG", unit="MWh", statistic_type=None),
        VariableDescription(name="DTG MRG", unit="MWh", statistic_type=None),
        VariableDescription(name="MAX MRG", unit="MWh", statistic_type=None),
        VariableDescription(name="NP COST", unit="Euro", statistic_type=None),
        VariableDescription(name="RES LOAD", unit="MWh", statistic_type=None),
        VariableDescription(name="NODU", unit=None, statistic_type=None),
        VariableDescription(name="ES_NUCLEAR_TH_PROD", unit="MWh", statistic_type=None),
        VariableDescription(name="FR_NUCLEAR_TH_PROD", unit="MWh", statistic_type=None),
    ]

    # check we get ES variables for ES, FR variables for FR
    assert area_dfs[1].variables == [
        VariableDescription(name="CO2 EMIS.", unit="Tons", statistic_type=None),
        VariableDescription(name="ES_NUCLEAR", unit="MWh", statistic_type=None),
        VariableDescription(name="AVL DTG", unit="MWh", statistic_type=None),
        VariableDescription(name="DTG MRG", unit="MWh", statistic_type=None),
        VariableDescription(name="MAX MRG", unit="MWh", statistic_type=None),
        VariableDescription(name="NP COST", unit="Euro", statistic_type=None),
        VariableDescription(name="NODU", unit=None, statistic_type=None),
        VariableDescription(name="RES LOAD", unit="MWh", statistic_type=None),
    ]

    assert area_dfs[2].variables == [
        VariableDescription(name="CO2 EMIS.", unit="Tons", statistic_type=None),
        VariableDescription(name="FR_NUCLEAR", unit="MWh", statistic_type=None),
        VariableDescription(name="AVL DTG", unit="MWh", statistic_type=None),
        VariableDescription(name="DTG MRG", unit="MWh", statistic_type=None),
        VariableDescription(name="MAX MRG", unit="MWh", statistic_type=None),
        VariableDescription(name="NP COST", unit="Euro", statistic_type=None),
        VariableDescription(name="NODU", unit=None, statistic_type=None),
        VariableDescription(name="RES LOAD", unit="MWh", statistic_type=None),
    ]

    # Check content for one column
    assert area_dfs[2].data.to_series(1).to_list() == [
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


def test_iterate_areas_filters(parquet_dir: Path, parquet_metadata: IParquetOutputMetadata) -> None:

    area_dfs = list(iterate_areas_df(parquet_metadata, parquet_dir, MatrixFrequency.MONTHLY, [1], [], []))

    assert [(a.year, a.area_id) for a in area_dfs] == [
        (1, "@ all areas"),
        (1, "es"),
        (1, "fr"),
    ]

    area_dfs = list(iterate_areas_df(parquet_metadata, parquet_dir, MatrixFrequency.MONTHLY, [1], ["fr"], []))

    assert [(a.year, a.area_id) for a in area_dfs] == [
        (1, "fr"),
    ]

    area_dfs = list(
        iterate_areas_df(parquet_metadata, parquet_dir, MatrixFrequency.MONTHLY, [1], ["fr"], ["FR_NUCLEAR"])
    )

    assert [(a.year, a.area_id) for a in area_dfs] == [
        (1, "fr"),
    ]
    assert area_dfs[0].variables == [VariableDescription(name="FR_NUCLEAR", unit="MWh", statistic_type=None)]
    assert area_dfs[0].data.columns == ["FR_NUCLEAR__MWh"]
    assert area_dfs[0].data.to_series(0).to_list() == [
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
