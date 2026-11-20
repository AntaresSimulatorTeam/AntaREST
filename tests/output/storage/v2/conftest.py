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
from antarest.output.storage.v2.dbmodel import DbParquetOutput
from antarest.output.storage.v2.metadata import IParquetOutputMetadata, ParquetOuputMetadataImpl
from antarest.output.storage.v2.variables_parsing import extract_output_variables_to_database
from antarest.output.storage.v2.variables_storage import create_parquet_files


@pytest.fixture
def output_dir(data_dir: Path) -> Path:
    return data_dir / "20260810-1420eco-thermal_groups"


@pytest.fixture
def parquet_dir(tmp_path: Path) -> Path:
    dir = tmp_path / "output"
    dir.mkdir()
    return dir


@pytest.fixture
def parquet_metadata(output_dir: Path, parquet_dir: Path, db_session: Session) -> IParquetOutputMetadata:
    """
    Imports 20260810-1420eco-thermal_groups to parquet and return the associated metadata
    """

    db_output = DbParquetOutput(id=0, mc_years=[1, 2])
    db_session.add(db_output)
    db_session.flush()

    file_output = FileOutput(output_dir)
    extract_output_variables_to_database(db_session, db_output.id, file_output)
    db_session.flush()

    output_metadata = ParquetOuputMetadataImpl(db_session, db_output.id)
    create_parquet_files(output_metadata, file_output, parquet_dir)

    assert len(list(parquet_dir.iterdir())) == 1
    monthly_file = parquet_dir / "mc-ind_areas_monthly.parquet"
    assert monthly_file.is_file()

    return output_metadata
