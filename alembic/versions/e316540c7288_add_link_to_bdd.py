"""add_link_to_bdd

Revision ID: e316540c7288
Revises: d2942741ae68
Create Date: 2025-08-18 10:41:53.613526

"""
from typing import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e316540c7288'
down_revision = 'd2942741ae68'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'link',
        sa.Column('study_id', sa.String(length=36), nullable=False),
        sa.Column('area1', sa.String(), nullable=False),
        sa.Column('area2', sa.String(), nullable=False),
        sa.Column('hurdles_cost', sa.Boolean(), nullable=False),
        sa.Column('loop_flow', sa.Boolean(), nullable=False),
        sa.Column('use_phase_shifter', sa.Boolean(), nullable=False),
        sa.Column(
            'transmission_capacities',
            sa.Enum('INFINITE', 'IGNORE', 'ENABLED', name='transmissioncapacity'),
            nullable=False
        ),
        sa.Column(
            'asset_type',
            sa.Enum('AC', 'DC', 'GAZ', 'VIRT', 'OTHER', name='assettype'),
            nullable=False
        ),
        sa.Column('display_comments', sa.Boolean(), nullable=False),
        sa.Column('comments', sa.String(), nullable=False),
        sa.Column('colorr', sa.Integer(), nullable=False),
        sa.Column('colorb', sa.Integer(), nullable=False),
        sa.Column('colorg', sa.Integer(), nullable=False),
        sa.Column('link_width', sa.Float(), nullable=False),
        sa.Column(
            'link_style',
            sa.Enum('DOT', 'PLAIN', 'DASH', 'DOT_DASH', 'OTHER', name='linkstyle'),
            nullable=False
        ),
        sa.Column('filter_synthesis', sa.String(), nullable=False),
        sa.Column('filter_year_by_year', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['study_id'], ['study.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('study_id', 'area1', 'area2')
    )


def downgrade() -> None:
    op.drop_table('link')
