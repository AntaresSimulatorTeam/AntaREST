"""create_link_table

Revision ID: 10318e5320f6
Revises: 6a6d36e3c6ed
Create Date: 2026-01-28 17:32:28.795223

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '10318e5320f6'
down_revision = '6a6d36e3c6ed'
branch_labels = None
depends_on = None


def upgrade():
    # 1- Create the Enums (PostgreSQL only)
    transmission_capacity_enum = sa.Enum('infinite', 'ignore', 'enabled', name="transmissioncapacity")
    asset_type_enum = sa.Enum('ac', 'dc', 'gaz', 'virt', 'other', name="assettype")
    link_style_enum = sa.Enum('dot', 'plain', 'dash', 'dotdash', 'other', name="linkstyle")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        transmission_capacity_enum.create(bind, checkfirst=True)
        asset_type_enum.create(bind, checkfirst=True)
        link_style_enum.create(bind, checkfirst=True)

    # 2- Create the table
    op.create_table("link",
    sa.Column("study_id", sa.String(length=36), nullable=False),
    sa.Column("area1", sa.String(length=255), nullable=False),
    sa.Column("area2", sa.String(length=255), nullable=False),
    sa.Column("hurdles_cost", sa.Boolean(), nullable=False),
    sa.Column("loop_flow", sa.Boolean(), nullable=False),
    sa.Column("use_phase_shifter", sa.Boolean(), nullable=False),
    sa.Column("transmission_capacities", transmission_capacity_enum, nullable=False),
    sa.Column("asset_type", asset_type_enum, nullable=False),
    sa.Column("display_comments", sa.Boolean(), nullable=False),
    sa.Column("comments", sa.String(), nullable=False),
    sa.Column("colorr", sa.Integer(), nullable=False),
    sa.Column("colorb", sa.Integer(), nullable=False),
    sa.Column("colorg", sa.Integer(), nullable=False),
    sa.Column("link_width", sa.Float(), nullable=False),
    sa.Column("link_style", link_style_enum, nullable=False),
    sa.Column("filter_synthesis", sa.String(), nullable=False),
    sa.Column("filter_year_by_year", sa.String(), nullable=False),
    sa.ForeignKeyConstraint(
        ["study_id", "area1"],
        ["area.study_id", "area.area_id"],
        name="fk_link_study_id_area_id_1",
        ondelete="CASCADE",
    ),
    sa.ForeignKeyConstraint(
        ["study_id", "area2"],
        ["area.study_id", "area.area_id"],
        name="fk_link_study_id_area_id_2",
        ondelete="CASCADE",
    ),
    sa.PrimaryKeyConstraint("study_id", "area1", "area2", name=op.f("pk_link")))

def downgrade():
    # Drop table
    op.drop_table("link")

    # Drop enum type (PostgreSQL only)
    if op.get_context().dialect.name == "postgresql":
        sa.Enum(name="transmissioncapacity").drop(op.get_bind(), checkfirst=True)
        sa.Enum(name="assettype").drop(op.get_bind(), checkfirst=True)
        sa.Enum(name="linkstyle").drop(op.get_bind(), checkfirst=True)
