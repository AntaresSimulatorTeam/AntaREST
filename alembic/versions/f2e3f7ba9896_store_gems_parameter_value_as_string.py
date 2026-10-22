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
from antarest.study.dao.database.models import study_data_id_col

# revision identifiers, used by Alembic.
revision = "f2e3f7ba9896"
down_revision = "b60aab4df757"
branch_labels = None
depends_on = None


def upgrade():
    # Data series must exist before `gems_component_parameters.dataseries_id` can reference them.
    op.create_table(
        "gems_data_series",
        study_data_id_col(primary_key=False),
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("values", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["study_data_id"], ["study_data.study_data_id"], name="fk_gems_data_series_study_data", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("study_data_id", "id", name="pk_gems_data_series"),
    )

    # `value` now stores either a fixed numeric value or the `id` of a data series (e.g.
    # "demand_profile") as text, since a GEMS parameter can be assigned either kind of value.
    with op.batch_alter_table("gems_component_parameters", schema=None) as batch_op:
        batch_op.alter_column(
            "value",
            existing_type=sa.Float(),
            type_=sa.String(length=255),
            existing_nullable=False,
            postgresql_using="value::varchar(255)",
        )
        batch_op.add_column(sa.Column("dataseries_id", sa.String(length=255), nullable=True))
        batch_op.create_check_constraint(
            "ck_gems_component_parameters_dataseries_id_matches_value",
            "dataseries_id IS NULL OR dataseries_id = value",
        )
        batch_op.create_check_constraint(
            "ck_gems_component_parameters_value_type_matches_dependency",
            "(dataseries_id IS NULL) = (NOT time_dependent AND NOT scenario_dependent)",
        )
        batch_op.create_foreign_key(
            "fk_gems_component_parameters_dataseries_id",
            "gems_data_series",
            ["study_data_id", "dataseries_id"],
            ["study_data_id", "id"],
        )


def downgrade():
    with op.batch_alter_table("gems_component_parameters", schema=None) as batch_op:
        batch_op.drop_constraint("fk_gems_component_parameters_dataseries_id", type_="foreignkey")
        batch_op.drop_constraint("ck_gems_component_parameters_value_type_matches_dependency", type_="check")
        batch_op.drop_constraint("ck_gems_component_parameters_dataseries_id_matches_value", type_="check")
        batch_op.drop_column("dataseries_id")
        batch_op.alter_column(
            "value",
            existing_type=sa.String(length=255),
            type_=sa.Float(),
            existing_nullable=False,
            postgresql_using="value::double precision",
        )

    op.drop_table("gems_data_series")
