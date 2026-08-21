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

from antarest.output.filestudy.model import FileOutput, VariableDescription
from antarest.output.storage.v2.dbmodel import DbParquetOutput
from antarest.output.storage.v2.variables_fetching import get_area_variables
from antarest.output.storage.v2.variables_parsing import extract_output_variables_to_database


@pytest.fixture
def output_dir(data_dir: Path) -> Path:
    return data_dir / "20260810-1420eco-thermal_groups"


def test_get_area_variables(db_session: Session, output_dir: Path) -> None:

    db_output = DbParquetOutput(id=0)
    db_session.add(db_output)
    db_session.flush()

    file_output = FileOutput(output_dir)
    extract_output_variables_to_database(db_session, db_output.id, file_output)
    db_session.flush()

    assert get_area_variables(db_session, db_output.id, "mc-ind", "fr") == [
        VariableDescription(name="CO2 EMIS.", unit="Tons", statistic_type=None),
        VariableDescription(name="FR_NUCLEAR", unit="MWh", statistic_type=None),
        VariableDescription(name="AVL DTG", unit="MWh", statistic_type=None),
        VariableDescription(name="DTG MRG", unit="MWh", statistic_type=None),
        VariableDescription(name="MAX MRG", unit="MWh", statistic_type=None),
        VariableDescription(name="NP COST", unit="Euro", statistic_type=None),
        VariableDescription(name="NODU", unit=None, statistic_type=None),
        VariableDescription(name="RES LOAD", unit="MWh", statistic_type=None),
    ]

    assert get_area_variables(db_session, db_output.id, "mc-ind", "es") == [
        VariableDescription(name="CO2 EMIS.", unit="Tons", statistic_type=None),
        VariableDescription(name="ES_NUCLEAR", unit="MWh", statistic_type=None),
        VariableDescription(name="AVL DTG", unit="MWh", statistic_type=None),
        VariableDescription(name="DTG MRG", unit="MWh", statistic_type=None),
        VariableDescription(name="MAX MRG", unit="MWh", statistic_type=None),
        VariableDescription(name="NP COST", unit="Euro", statistic_type=None),
        VariableDescription(name="NODU", unit=None, statistic_type=None),
        VariableDescription(name="RES LOAD", unit="MWh", statistic_type=None),
    ]

    assert get_area_variables(db_session, db_output.id, "mc-all", "es") == [
        VariableDescription(name="CO2 EMIS.", unit="Tons", statistic_type="EXP"),
        VariableDescription(name="CO2 EMIS.", unit="Tons", statistic_type="std"),
        VariableDescription(name="CO2 EMIS.", unit="Tons", statistic_type="min"),
        VariableDescription(name="CO2 EMIS.", unit="Tons", statistic_type="max"),
        VariableDescription(name="ES_NUCLEAR", unit="MWh", statistic_type="EXP"),
        VariableDescription(name="ES_NUCLEAR", unit="MWh", statistic_type="std"),
        VariableDescription(name="ES_NUCLEAR", unit="MWh", statistic_type="min"),
        VariableDescription(name="ES_NUCLEAR", unit="MWh", statistic_type="max"),
        VariableDescription(name="AVL DTG", unit="MWh", statistic_type="EXP"),
        VariableDescription(name="AVL DTG", unit="MWh", statistic_type="std"),
        VariableDescription(name="AVL DTG", unit="MWh", statistic_type="min"),
        VariableDescription(name="AVL DTG", unit="MWh", statistic_type="max"),
        VariableDescription(name="DTG MRG", unit="MWh", statistic_type="EXP"),
        VariableDescription(name="DTG MRG", unit="MWh", statistic_type="std"),
        VariableDescription(name="DTG MRG", unit="MWh", statistic_type="min"),
        VariableDescription(name="DTG MRG", unit="MWh", statistic_type="max"),
        VariableDescription(name="MAX MRG", unit="MWh", statistic_type="EXP"),
        VariableDescription(name="MAX MRG", unit="MWh", statistic_type="std"),
        VariableDescription(name="MAX MRG", unit="MWh", statistic_type="min"),
        VariableDescription(name="MAX MRG", unit="MWh", statistic_type="max"),
        VariableDescription(name="NP COST", unit="Euro", statistic_type="EXP"),
        VariableDescription(name="NP COST", unit="Euro", statistic_type="std"),
        VariableDescription(name="NP COST", unit="Euro", statistic_type="min"),
        VariableDescription(name="NP COST", unit="Euro", statistic_type="max"),
        VariableDescription(name="NODU", unit=None, statistic_type="EXP"),
        VariableDescription(name="NODU", unit=None, statistic_type="std"),
        VariableDescription(name="NODU", unit=None, statistic_type="min"),
        VariableDescription(name="NODU", unit=None, statistic_type="max"),
        VariableDescription(name="RES LOAD", unit="MWh", statistic_type="EXP"),
        VariableDescription(name="RES LOAD", unit="MWh", statistic_type="std"),
        VariableDescription(name="RES LOAD", unit="MWh", statistic_type="min"),
        VariableDescription(name="RES LOAD", unit="MWh", statistic_type="max"),
    ]
