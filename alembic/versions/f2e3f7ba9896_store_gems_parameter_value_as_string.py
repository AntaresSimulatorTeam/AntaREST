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

"""store_gems_parameter_value_as_string

Revision ID: f2e3f7ba9896
Revises: b60aab4df757
Create Date: 2026-10-08 16:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "f2e3f7ba9896"
down_revision = "b60aab4df757"
branch_labels = None
depends_on = None


def upgrade():

    # `value` only holds the float for constant parameters; for time-/scenario-dependent parameters
    # it is NULL and `matrix_id` references the matrix in the matrix store instead.
    with op.batch_alter_table("gems_component_parameters", schema=None) as batch_op:
        batch_op.alter_column(
            "value",
            existing_type=sa.Float(),
            nullable=True,
        )
        batch_op.add_column(sa.Column("matrix_id", sa.String(length=64), nullable=True))
        batch_op.create_check_constraint(
            "ck_gems_component_parameters_matrix_id_matches_dependent",
            "(matrix_id IS NULL) = (NOT time_dependent AND NOT scenario_dependent)",
        )
        batch_op.create_check_constraint(
            "ck_gems_component_parameters_value_matches_dependent",
            "(value IS NULL) =  (time_dependent OR scenario_dependent)",
        )


def downgrade():
    with op.batch_alter_table("gems_component_parameters", schema=None) as batch_op:
        batch_op.drop_constraint("ck_gems_component_parameters_value_matches_dependent", type_="check")
        batch_op.drop_constraint("ck_gems_component_parameters_matrix_id_matches_dependent", type_="check")
        batch_op.drop_column("matrix_id")
        batch_op.alter_column(
            "value",
            existing_type=sa.Float(),
            nullable=False,
        )
