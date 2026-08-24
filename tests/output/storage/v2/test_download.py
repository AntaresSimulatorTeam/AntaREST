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
from sqlalchemy.orm import Session

from antarest.output.filestudy.model import FileOutput
from antarest.output.model import StudyDownloadDTO, StudyDownloadType
from antarest.output.storage.v2.dbmodel import DbParquetOutput
from antarest.output.storage.v2.download import (
    build_matrix_aggregation_result,
)
from antarest.output.storage.v2.metadata import ParquetOuputMetadataImpl
from antarest.output.storage.v2.variables_fetching import get_variables_index
from antarest.output.storage.v2.variables_parsing import extract_output_variables_to_database
from antarest.output.storage.v2.variables_storage import extract_areas_refacto
from antarest.study.model import MatrixFrequency


@pytest.fixture
def output_dir(data_dir: Path) -> Path:
    return data_dir / "20260810-1420eco-thermal_groups"


def test_download_areas(output_dir: Path, db_session: Session, tmp_path: Path) -> None:
    # TODO: simplify setup

    # Setup

    db_output = DbParquetOutput(id=0, playlist=[1, 2])
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

    assert len(list(target_dir.iterdir())) == 1
    monthly_file = target_dir / "mc-ind_areas_monthly.parquet"
    assert monthly_file.is_file()

    # Actual test

    output_metadata = ParquetOuputMetadataImpl(db_session, db_output.id)
    data_selection = StudyDownloadDTO(type=StudyDownloadType.AREA, years=[], level=MatrixFrequency.MONTHLY, filter=[])
    aggregate = build_matrix_aggregation_result(output_metadata, target_dir, data_selection)

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


def test_download_district(output_dir: Path, db_session: Session, tmp_path: Path) -> None:
    # TODO: simplify setup
    # TODO: make it pass

    # Setup

    db_output = DbParquetOutput(id=0, playlist=[1, 2])
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

    assert len(list(target_dir.iterdir())) == 1
    monthly_file = target_dir / "mc-ind_areas_monthly.parquet"
    assert monthly_file.is_file()

    # Actual test

    output_metadata = ParquetOuputMetadataImpl(db_session, db_output.id)

    data_selection = StudyDownloadDTO(type=StudyDownloadType.DISTRICT, years=[1], level=MatrixFrequency.MONTHLY)
    aggregate = build_matrix_aggregation_result(output_metadata, target_dir, data_selection)

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
