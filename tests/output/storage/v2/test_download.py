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

from antarest.output.model import StudyDownloadDTO, StudyDownloadType
from antarest.output.storage.v2.download import (
    build_matrix_aggregation_result,
)
from antarest.output.storage.v2.metadata import IParquetOutputMetadata
from antarest.study.model import MatrixFrequency


def test_download_areas(parquet_dir: Path, parquet_metadata: IParquetOutputMetadata) -> None:

    data_selection = StudyDownloadDTO(type=StudyDownloadType.AREA, years=[], level=MatrixFrequency.MONTHLY, filter=[])
    aggregate = build_matrix_aggregation_result(parquet_metadata, parquet_dir, data_selection)

    year1_st_by_area = {data.name: data.data["1"] for data in aggregate.data}
    es_variables = [ts.name for ts in year1_st_by_area["es"]]
    fr_variables = [ts.name for ts in year1_st_by_area["fr"]]

    # Same test as for filestudy
    assert es_variables == [
        "CO2 EMIS.",
        "ES_NUCLEAR",  # We only get ES group
        "AVL DTG",
        "DTG MRG",
        "MAX MRG",
        "NP COST",
        "NODU",
        "RES LOAD",
    ]
    assert fr_variables == [
        "CO2 EMIS.",
        "FR_NUCLEAR",  # we only get FR group
        "AVL DTG",
        "DTG MRG",
        "MAX MRG",
        "NP COST",
        "NODU",
        "RES LOAD",
    ]


def test_download_district(parquet_dir: Path, parquet_metadata: IParquetOutputMetadata) -> None:

    # Like in filesystem implementation, DISTRICT is handled identically to AREA ...

    data_selection = StudyDownloadDTO(type=StudyDownloadType.DISTRICT, years=[1], level=MatrixFrequency.MONTHLY)
    aggregate = build_matrix_aggregation_result(parquet_metadata, parquet_dir, data_selection)

    year1_st_by_area = {data.name: data.data["1"] for data in aggregate.data}
    all_areas_variables = [ts.name for ts in year1_st_by_area["@ all areas"]]

    assert all_areas_variables == [
        "CO2 EMIS.",
        "AVL DTG",
        "DTG MRG",
        "MAX MRG",
        "NP COST",
        "RES LOAD",
        "NODU",
        "ES_NUCLEAR_TH_PROD",
        "FR_NUCLEAR_TH_PROD",
    ]
