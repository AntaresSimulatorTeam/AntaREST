"""add_area_properties_table

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
    op.create_table(
        "area_properties",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("area_id", sa.String(length=255), nullable=False),
        sa.Column("energy_cost_unsupplied", sa.Float(), nullable=False),
        sa.Column("energy_cost_spilled", sa.Float(), nullable=False),
        sa.Column("non_dispatch_power", sa.Boolean(), nullable=False),
        sa.Column("dispatch_hydro_power", sa.Boolean(), nullable=False),
        sa.Column("other_dispatch_power", sa.Boolean(), nullable=False),
        sa.Column("spread_unsupplied_energy_cost", sa.Float(), nullable=False),
        sa.Column("spread_spilled_energy_cost", sa.Float(), nullable=False),
        sa.Column("filter_synthesis", sa.Text(), nullable=False),
        sa.Column("filter_by_year", sa.Text(), nullable=False),
        sa.Column("adequacy_patch_mode", sa.Enum('outside', 'inside', 'virtual', name='adequacypatchmode'), nullable=True),
        sa.ForeignKeyConstraint(
            ["study_id", "area_id"],
            ["area.study_id", "area.area_id"],
            name=op.f("fk_area_properties_study_id_area_id_area"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("study_id", "area_id", name=op.f("pk_area_properties")),
    )


def downgrade() -> None:
    op.drop_table("area_properties")
