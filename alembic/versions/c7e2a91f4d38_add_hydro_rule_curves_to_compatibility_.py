"""add_hydro_rule_curves_to_compatibility_parameters

Revision ID: c7e2a91f4d38
Revises: 193aa1d7b5ad
Create Date: 2026-10-29 10:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "c7e2a91f4d38"
down_revision = "193aa1d7b5ad"
branch_labels = None
depends_on = None


def upgrade() -> None:
    hydro_rule_curves_enum = sa.Enum("scenarized", "single", name="hydrorulecurves")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        hydro_rule_curves_enum.create(bind, checkfirst=True)

    with op.batch_alter_table("compatibility_parameters") as batch_op:
        batch_op.add_column(sa.Column("hydro_rule_curves", hydro_rule_curves_enum, nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("compatibility_parameters") as batch_op:
        batch_op.drop_column("hydro_rule_curves")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        sa.Enum(name="hydrorulecurves").drop(bind, checkfirst=True)
