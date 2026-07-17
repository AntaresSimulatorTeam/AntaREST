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

import pytest

from antarest.output.model import StudyDownloadDTO, StudyDownloadType
from antarest.output.storage.file.abstract_storage import build_matrix_aggregation_result
from antarest.study.model import MatrixFrequency


@pytest.fixture
def sta_mini_zip_path(project_path: Path) -> Path:
    return project_path / "examples/studies/STA-mini.zip"


@pytest.fixture
def outputs_path(tmp_path: Path, sta_mini_zip_path: Path) -> Path:
    target = tmp_path / "STA-mini"
    with zipfile.ZipFile(sta_mini_zip_path, "r") as zf:
        zf.extractall(target)
    return target / "STA-mini" / "output"


def test_file_output_to_matrix_aggregation_result_areas(outputs_path: Path):
    output_path = outputs_path / "20201014-1425eco-goodbye"
    annual_result = {
        "index": {"start_date": "2018-01-01 00:00:00", "steps": 1, "first_week_size": 7, "level": "annual"},
        "data": [
            {
                "type": "AREA",
                "name": "de",
                "data": {
                    "1": [
                        {"name": "OV. COST", "unit": "Euro", "data": [92904000.0]},
                        {"name": "OP. COST", "unit": "Euro", "data": [92904000.0]},
                        {"name": "MRG. PRICE", "unit": "Euro", "data": [47.14]},
                        {"name": "CO2 EMIS.", "unit": "Tons", "data": [0.0]},
                        {"name": "BALANCE", "unit": "MWh", "data": [0.0]},
                        {"name": "ROW BAL.", "unit": "MWh", "data": [0.0]},
                        {"name": "PSP", "unit": "MWh", "data": [0.0]},
                        {"name": "MISC. NDG", "unit": "MWh", "data": [0.0]},
                        {"name": "LOAD", "unit": "MWh", "data": [2805600.0]},
                        {"name": "H. ROR", "unit": "MWh", "data": [0.0]},
                        {"name": "WIND", "unit": "MWh", "data": [0.0]},
                        {"name": "SOLAR", "unit": "MWh", "data": [0.0]},
                        {"name": "NUCLEAR", "unit": "MWh", "data": [0.0]},
                        {"name": "LIGNITE", "unit": "MWh", "data": [0.0]},
                        {"name": "COAL", "unit": "MWh", "data": [0.0]},
                        {"name": "GAS", "unit": "MWh", "data": [0.0]},
                        {"name": "OIL", "unit": "MWh", "data": [0.0]},
                        {"name": "MIX. FUEL", "unit": "MWh", "data": [0.0]},
                        {"name": "MISC. DTG", "unit": "MWh", "data": [2805600.0]},
                        {"name": "H. STOR", "unit": "MWh", "data": [0.0]},
                        {"name": "H. PUMP", "unit": "MWh", "data": [0.0]},
                        {"name": "H. LEV", "unit": "%", "data": [None]},
                        {"name": "H. INFL", "unit": "MWh", "data": [0.0]},
                        {"name": "H. OVFL", "unit": "%", "data": [None]},
                        {"name": "H. VAL", "unit": "Euro/MWh", "data": [None]},
                        {"name": "H. COST", "unit": "Euro", "data": [0.0]},
                        {"name": "UNSP. ENRG", "unit": "MWh", "data": [0.0]},
                        {"name": "SPIL. ENRG", "unit": "MWh", "data": [0.0]},
                        {"name": "LOLD", "unit": "Hours", "data": [0.0]},
                        {"name": "LOLP", "unit": "%", "data": [0.0]},
                        {"name": "AVL DTG", "unit": "MWh", "data": [6048000.0]},
                        {"name": "DTG MRG", "unit": "MWh", "data": [3242400.0]},
                        {"name": "MAX MRG", "unit": "MWh", "data": [3242400.0]},
                        {"name": "NP COST", "unit": "Euro", "data": [0.0]},
                        {"name": "NODU", "unit": "", "data": [1566.0]},
                    ],
                    "2": [
                        {"name": "OV. COST", "unit": "Euro", "data": [92904000.0]},
                        {"name": "OP. COST", "unit": "Euro", "data": [92904000.0]},
                        {"name": "MRG. PRICE", "unit": "Euro", "data": [47.14]},
                        {"name": "CO2 EMIS.", "unit": "Tons", "data": [0.0]},
                        {"name": "BALANCE", "unit": "MWh", "data": [0.0]},
                        {"name": "ROW BAL.", "unit": "MWh", "data": [0.0]},
                        {"name": "PSP", "unit": "MWh", "data": [0.0]},
                        {"name": "MISC. NDG", "unit": "MWh", "data": [0.0]},
                        {"name": "LOAD", "unit": "MWh", "data": [2805600.0]},
                        {"name": "H. ROR", "unit": "MWh", "data": [0.0]},
                        {"name": "WIND", "unit": "MWh", "data": [0.0]},
                        {"name": "SOLAR", "unit": "MWh", "data": [0.0]},
                        {"name": "NUCLEAR", "unit": "MWh", "data": [0.0]},
                        {"name": "LIGNITE", "unit": "MWh", "data": [0.0]},
                        {"name": "COAL", "unit": "MWh", "data": [0.0]},
                        {"name": "GAS", "unit": "MWh", "data": [0.0]},
                        {"name": "OIL", "unit": "MWh", "data": [0.0]},
                        {"name": "MIX. FUEL", "unit": "MWh", "data": [0.0]},
                        {"name": "MISC. DTG", "unit": "MWh", "data": [2805600.0]},
                        {"name": "H. STOR", "unit": "MWh", "data": [0.0]},
                        {"name": "H. PUMP", "unit": "MWh", "data": [0.0]},
                        {"name": "H. LEV", "unit": "%", "data": [None]},
                        {"name": "H. INFL", "unit": "MWh", "data": [0.0]},
                        {"name": "H. OVFL", "unit": "%", "data": [None]},
                        {"name": "H. VAL", "unit": "Euro/MWh", "data": [None]},
                        {"name": "H. COST", "unit": "Euro", "data": [0.0]},
                        {"name": "UNSP. ENRG", "unit": "MWh", "data": [0.0]},
                        {"name": "SPIL. ENRG", "unit": "MWh", "data": [0.0]},
                        {"name": "LOLD", "unit": "Hours", "data": [0.0]},
                        {"name": "LOLP", "unit": "%", "data": [0.0]},
                        {"name": "AVL DTG", "unit": "MWh", "data": [6048000.0]},
                        {"name": "DTG MRG", "unit": "MWh", "data": [3242400.0]},
                        {"name": "MAX MRG", "unit": "MWh", "data": [3242400.0]},
                        {"name": "NP COST", "unit": "Euro", "data": [0.0]},
                        {"name": "NODU", "unit": "", "data": [1566.0]},
                    ],
                },
            },
            {
                "type": "AREA",
                "name": "es",
                "data": {
                    "1": [
                        {"name": "OV. COST", "unit": "Euro", "data": [92904000.0]},
                        {"name": "OP. COST", "unit": "Euro", "data": [92904000.0]},
                        {"name": "MRG. PRICE", "unit": "Euro", "data": [47.14]},
                        {"name": "CO2 EMIS.", "unit": "Tons", "data": [0.0]},
                        {"name": "BALANCE", "unit": "MWh", "data": [0.0]},
                        {"name": "ROW BAL.", "unit": "MWh", "data": [0.0]},
                        {"name": "PSP", "unit": "MWh", "data": [0.0]},
                        {"name": "MISC. NDG", "unit": "MWh", "data": [0.0]},
                        {"name": "LOAD", "unit": "MWh", "data": [2805600.0]},
                        {"name": "H. ROR", "unit": "MWh", "data": [0.0]},
                        {"name": "WIND", "unit": "MWh", "data": [0.0]},
                        {"name": "SOLAR", "unit": "MWh", "data": [0.0]},
                        {"name": "NUCLEAR", "unit": "MWh", "data": [0.0]},
                        {"name": "LIGNITE", "unit": "MWh", "data": [0.0]},
                        {"name": "COAL", "unit": "MWh", "data": [0.0]},
                        {"name": "GAS", "unit": "MWh", "data": [0.0]},
                        {"name": "OIL", "unit": "MWh", "data": [0.0]},
                        {"name": "MIX. FUEL", "unit": "MWh", "data": [0.0]},
                        {"name": "MISC. DTG", "unit": "MWh", "data": [2805600.0]},
                        {"name": "H. STOR", "unit": "MWh", "data": [0.0]},
                        {"name": "H. PUMP", "unit": "MWh", "data": [0.0]},
                        {"name": "H. LEV", "unit": "%", "data": [None]},
                        {"name": "H. INFL", "unit": "MWh", "data": [0.0]},
                        {"name": "H. OVFL", "unit": "%", "data": [None]},
                        {"name": "H. VAL", "unit": "Euro/MWh", "data": [None]},
                        {"name": "H. COST", "unit": "Euro", "data": [0.0]},
                        {"name": "UNSP. ENRG", "unit": "MWh", "data": [0.0]},
                        {"name": "SPIL. ENRG", "unit": "MWh", "data": [0.0]},
                        {"name": "LOLD", "unit": "Hours", "data": [0.0]},
                        {"name": "LOLP", "unit": "%", "data": [0.0]},
                        {"name": "AVL DTG", "unit": "MWh", "data": [6048000.0]},
                        {"name": "DTG MRG", "unit": "MWh", "data": [3242400.0]},
                        {"name": "MAX MRG", "unit": "MWh", "data": [3242400.0]},
                        {"name": "NP COST", "unit": "Euro", "data": [0.0]},
                        {"name": "NODU", "unit": "", "data": [1566.0]},
                    ],
                    "2": [
                        {"name": "OV. COST", "unit": "Euro", "data": [92904000.0]},
                        {"name": "OP. COST", "unit": "Euro", "data": [92904000.0]},
                        {"name": "MRG. PRICE", "unit": "Euro", "data": [47.14]},
                        {"name": "CO2 EMIS.", "unit": "Tons", "data": [0.0]},
                        {"name": "BALANCE", "unit": "MWh", "data": [0.0]},
                        {"name": "ROW BAL.", "unit": "MWh", "data": [0.0]},
                        {"name": "PSP", "unit": "MWh", "data": [0.0]},
                        {"name": "MISC. NDG", "unit": "MWh", "data": [0.0]},
                        {"name": "LOAD", "unit": "MWh", "data": [2805600.0]},
                        {"name": "H. ROR", "unit": "MWh", "data": [0.0]},
                        {"name": "WIND", "unit": "MWh", "data": [0.0]},
                        {"name": "SOLAR", "unit": "MWh", "data": [0.0]},
                        {"name": "NUCLEAR", "unit": "MWh", "data": [0.0]},
                        {"name": "LIGNITE", "unit": "MWh", "data": [0.0]},
                        {"name": "COAL", "unit": "MWh", "data": [0.0]},
                        {"name": "GAS", "unit": "MWh", "data": [0.0]},
                        {"name": "OIL", "unit": "MWh", "data": [0.0]},
                        {"name": "MIX. FUEL", "unit": "MWh", "data": [0.0]},
                        {"name": "MISC. DTG", "unit": "MWh", "data": [2805600.0]},
                        {"name": "H. STOR", "unit": "MWh", "data": [0.0]},
                        {"name": "H. PUMP", "unit": "MWh", "data": [0.0]},
                        {"name": "H. LEV", "unit": "%", "data": [None]},
                        {"name": "H. INFL", "unit": "MWh", "data": [0.0]},
                        {"name": "H. OVFL", "unit": "%", "data": [None]},
                        {"name": "H. VAL", "unit": "Euro/MWh", "data": [None]},
                        {"name": "H. COST", "unit": "Euro", "data": [0.0]},
                        {"name": "UNSP. ENRG", "unit": "MWh", "data": [0.0]},
                        {"name": "SPIL. ENRG", "unit": "MWh", "data": [0.0]},
                        {"name": "LOLD", "unit": "Hours", "data": [0.0]},
                        {"name": "LOLP", "unit": "%", "data": [0.0]},
                        {"name": "AVL DTG", "unit": "MWh", "data": [6048000.0]},
                        {"name": "DTG MRG", "unit": "MWh", "data": [3242400.0]},
                        {"name": "MAX MRG", "unit": "MWh", "data": [3242400.0]},
                        {"name": "NP COST", "unit": "Euro", "data": [0.0]},
                        {"name": "NODU", "unit": "", "data": [1566.0]},
                    ],
                },
            },
        ],
    }

    data = StudyDownloadDTO(type=StudyDownloadType.AREA, level=MatrixFrequency.ANNUAL)
    res = build_matrix_aggregation_result(output_path, data)
    assert res.model_dump() == annual_result


def test_file_output_to_matrix_aggregation_result_with_clusters(outputs_path: Path):
    output_path = outputs_path / "20201014-1425eco-goodbye"
    annual_result = {
        "index": {"start_date": "2018-01-01 00:00:00", "steps": 1, "first_week_size": 7, "level": "annual"},
        "data": [
            {
                "type": "AREA",
                "name": "de",
                "data": {
                    "1": [
                        {"name": "OV. COST", "unit": "Euro", "data": [92904000.0]},
                        {"name": "OP. COST", "unit": "Euro", "data": [92904000.0]},
                        {"name": "MRG. PRICE", "unit": "Euro", "data": [47.14]},
                        {"name": "CO2 EMIS.", "unit": "Tons", "data": [0.0]},
                        {"name": "BALANCE", "unit": "MWh", "data": [0.0]},
                        {"name": "ROW BAL.", "unit": "MWh", "data": [0.0]},
                        {"name": "PSP", "unit": "MWh", "data": [0.0]},
                        {"name": "MISC. NDG", "unit": "MWh", "data": [0.0]},
                        {"name": "LOAD", "unit": "MWh", "data": [2805600.0]},
                        {"name": "H. ROR", "unit": "MWh", "data": [0.0]},
                        {"name": "WIND", "unit": "MWh", "data": [0.0]},
                        {"name": "SOLAR", "unit": "MWh", "data": [0.0]},
                        {"name": "NUCLEAR", "unit": "MWh", "data": [0.0]},
                        {"name": "LIGNITE", "unit": "MWh", "data": [0.0]},
                        {"name": "COAL", "unit": "MWh", "data": [0.0]},
                        {"name": "GAS", "unit": "MWh", "data": [0.0]},
                        {"name": "OIL", "unit": "MWh", "data": [0.0]},
                        {"name": "MIX. FUEL", "unit": "MWh", "data": [0.0]},
                        {"name": "MISC. DTG", "unit": "MWh", "data": [2805600.0]},
                        {"name": "H. STOR", "unit": "MWh", "data": [0.0]},
                        {"name": "H. PUMP", "unit": "MWh", "data": [0.0]},
                        {"name": "H. LEV", "unit": "%", "data": [None]},
                        {"name": "H. INFL", "unit": "MWh", "data": [0.0]},
                        {"name": "H. OVFL", "unit": "%", "data": [None]},
                        {"name": "H. VAL", "unit": "Euro/MWh", "data": [None]},
                        {"name": "H. COST", "unit": "Euro", "data": [0.0]},
                        {"name": "UNSP. ENRG", "unit": "MWh", "data": [0.0]},
                        {"name": "SPIL. ENRG", "unit": "MWh", "data": [0.0]},
                        {"name": "LOLD", "unit": "Hours", "data": [0.0]},
                        {"name": "LOLP", "unit": "%", "data": [0.0]},
                        {"name": "AVL DTG", "unit": "MWh", "data": [6048000.0]},
                        {"name": "DTG MRG", "unit": "MWh", "data": [3242400.0]},
                        {"name": "MAX MRG", "unit": "MWh", "data": [3242400.0]},
                        {"name": "NP COST", "unit": "Euro", "data": [0.0]},
                        {"name": "NODU", "unit": "", "data": [1566.0]},
                        {"name": "01_solar", "unit": "MWh", "data": [630000.0]},
                        {"name": "02_wind_on", "unit": "MWh", "data": [550000.0]},
                        {"name": "03_wind_off", "unit": "MWh", "data": [470000.0]},
                        {"name": "04_res", "unit": "MWh", "data": [390000.0]},
                        {"name": "05_nuclear", "unit": "MWh", "data": [310000.0]},
                        {"name": "06_coal", "unit": "MWh", "data": [230000.0]},
                        {"name": "07_gas", "unit": "MWh", "data": [150000.0]},
                        {"name": "08_non-res", "unit": "MWh", "data": [70000.0]},
                        {"name": "09_hydro_pump", "unit": "MWh", "data": [5600.0]},
                        {"name": "01_solar", "unit": "NP Cost - Euro", "data": [0.0]},
                        {"name": "02_wind_on", "unit": "NP Cost - Euro", "data": [0.0]},
                        {"name": "03_wind_off", "unit": "NP Cost - Euro", "data": [0.0]},
                        {"name": "04_res", "unit": "NP Cost - Euro", "data": [0.0]},
                        {"name": "05_nuclear", "unit": "NP Cost - Euro", "data": [0.0]},
                        {"name": "06_coal", "unit": "NP Cost - Euro", "data": [0.0]},
                        {"name": "07_gas", "unit": "NP Cost - Euro", "data": [0.0]},
                        {"name": "08_non-res", "unit": "NP Cost - Euro", "data": [0.0]},
                        {"name": "09_hydro_pump", "unit": "NP Cost - Euro", "data": [0.0]},
                        {"name": "01_solar", "unit": "NODU", "data": [334.0]},
                        {"name": "02_wind_on", "unit": "NODU", "data": [294.0]},
                        {"name": "03_wind_off", "unit": "NODU", "data": [254.0]},
                        {"name": "04_res", "unit": "NODU", "data": [214.0]},
                        {"name": "05_nuclear", "unit": "NODU", "data": [174.0]},
                        {"name": "06_coal", "unit": "NODU", "data": [134.0]},
                        {"name": "07_gas", "unit": "NODU", "data": [94.0]},
                        {"name": "08_non-res", "unit": "NODU", "data": [54.0]},
                        {"name": "09_hydro_pump", "unit": "NODU", "data": [14.0]},
                    ]
                },
            }
        ],
    }
    data = StudyDownloadDTO(
        type=StudyDownloadType.AREA, level=MatrixFrequency.ANNUAL, years=[1], filter=["de"], include_clusters=True
    )
    res = build_matrix_aggregation_result(output_path, data)
    assert res.model_dump() == annual_result


def test_file_output_to_matrix_aggregation_result_links(outputs_path: Path):
    output_path = outputs_path / "20241807-1540eco-extra-outputs"
    link_result = {
        "index": {"start_date": "2018-01-01 00:00:00", "steps": 1, "first_week_size": 7, "level": "annual"},
        "data": [
            {
                "type": "LINK",
                "name": "de^fr",
                "data": {
                    "1": [
                        {"name": "FLOW LIN.", "unit": "MWh", "data": [0.0]},
                        {"name": "UCAP LIN.", "unit": "MWh", "data": [0.0]},
                    ]
                },
            }
        ],
    }
    data = StudyDownloadDTO(
        type=StudyDownloadType.LINK, level=MatrixFrequency.ANNUAL, columns=["FLOW LIN.", "UCAP LIN."]
    )
    res = build_matrix_aggregation_result(output_path, data)
    assert res.model_dump() == link_result
