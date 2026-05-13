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

"""
Design:
variables metadata are stored in tables so that we can retrieve for each variable:
 - its name
 - its unit
 - the statistic name

and so that we know for each object of the study what were the output variables for that object.
"""

from sqlalchemy import Column, ForeignKeyConstraint, Integer, String, Table, UniqueConstraint

from antarest.dbmodel import Base

metadata = Base.metadata


OUTPUT_VARIABLES_TABLE = Table(
    "output_variables",
    metadata,
    Column("study_id", String, primary_key=True),
    Column("output_id", String, primary_key=True),
    Column("id", Integer, primary_key=True),  # an integer ID inside the output
    Column("name", String),
    Column("unit", String),
    Column("stat", String),  # enum ?
    Column("column", Integer),
    ForeignKeyConstraint(
        columns=("study_id", "output_id"),
        refcolumns=("output_v2_metadata.study_id", "output_v2_metadata.output_name"),
        name="fk_output_variables_output_v2_metadata",
        ondelete="CASCADE",
    ),
    UniqueConstraint(),
)


AREA_VARIABLES_TABLE = Table(
    "area_variables",
    metadata,
    Column("study_id", String, primary_key=True),
    Column("output_id", String, primary_key=True),
    Column("area_id", String, primary_key=True),
    Column("variable_id", Integer, primary_key=True),
    ForeignKeyConstraint(
        columns=("study_id", "output_id", "variable_id"),
        refcolumns=("", "output_v2_metadata.output_name", "area.id"),
        name="fk_area_variables_output_v2_metadata",
        ondelete="CASCADE",
    ),
)
