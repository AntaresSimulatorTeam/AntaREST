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

import pytest

from antarest.output.filestudy.download import build_matrix_aggregation_result
from antarest.output.model import StudyDownloadDTO, StudyDownloadType
from antarest.study.model import MatrixFrequency


@pytest.fixture
def output_dir(data_dir: Path) -> Path:
    return data_dir / "20260810-1420eco-thermal_groups"


def test_build_aggregates__different_thermal_groups(output_dir: Path) -> None:
    """
    Checks that when areas have different variables, we only get the relevant ones for each area.
    Here areas fr and es have different thermal groups.
    """
    download = StudyDownloadDTO(
        type=StudyDownloadType.AREA,
        years=[1],
        level=MatrixFrequency.MONTHLY,
    )
    aggregate = build_matrix_aggregation_result(output_dir, download)

    year1_st_by_area = {data.name: data.data["1"] for data in aggregate.data}
    es_variables = [ts.name for ts in year1_st_by_area["es"]]
    fr_variables = [ts.name for ts in year1_st_by_area["fr"]]

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


def test_build_aggregates__district(output_dir: Path) -> None:

    download = StudyDownloadDTO(
        type=StudyDownloadType.DISTRICT,
        years=[1],
        level=MatrixFrequency.MONTHLY,
    )
    aggregate = build_matrix_aggregation_result(output_dir, download)

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
