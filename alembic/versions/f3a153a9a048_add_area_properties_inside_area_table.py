"""add_area_properties_inside_area_table

Revision ID: f3a153a9a048
Revises: 2572145aff71
Create Date: 2026-01-22 16:52:39.879743

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f3a153a9a048'
down_revision = '2572145aff71'
branch_labels = None
depends_on = None



def upgrade() -> None:
    with op.batch_alter_table("area", schema=None) as batch_op:
        batch_op.add_column(sa.Column("energy_cost_unsupplied", sa.Float(), nullable=False))
        batch_op.add_column(sa.Column("energy_cost_spilled", sa.Float(), nullable=False))
        batch_op.add_column(sa.Column("non_dispatch_power", sa.Boolean(), nullable=False))
        batch_op.add_column(sa.Column("dispatch_hydro_power", sa.Boolean(), nullable=False))
        batch_op.add_column(sa.Column("other_dispatch_power", sa.Boolean(), nullable=False))
        batch_op.add_column(sa.Column("spread_unsupplied_energy_cost", sa.Float(), nullable=False))
        batch_op.add_column(sa.Column("spread_spilled_energy_cost", sa.Float(), nullable=False))
        batch_op.add_column(sa.Column("filter_synthesis", sa.String(), nullable=False))
        batch_op.add_column(sa.Column("filter_by_year", sa.String(), nullable=False))
        batch_op.add_column(sa.Column("adequacy_patch_mode", sa.Enum('outside', 'inside', 'virtual', name='adequacypatchmode'), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('area') as batch_op:
        batch_op.drop_column('energy_cost_unsupplied')
        batch_op.drop_column('energy_cost_spilled')
        batch_op.drop_column('non_dispatch_power')
        batch_op.drop_column('dispatch_hydro_power')
        batch_op.drop_column('other_dispatch_power')
        batch_op.drop_column('spread_unsupplied_energy_cost')
        batch_op.drop_column('spread_spilled_energy_cost')
        batch_op.drop_column('filter_synthesis')
        batch_op.drop_column('filter_by_year')
        batch_op.drop_column('adequacy_patch_mode')

        # Drop enum type (PostgreSQL only)
        if op.get_context().dialect.name == "postgresql":
            sa.Enum(name="adequacypatchmode").drop(op.get_bind(), checkfirst=True)
