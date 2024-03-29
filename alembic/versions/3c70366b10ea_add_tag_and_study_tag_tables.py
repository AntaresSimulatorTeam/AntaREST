"""Add tag and study_tag tables

Revision ID: 3c70366b10ea
Revises: 1f5db5dfad80
Create Date: 2024-02-02 13:06:47.627554

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "3c70366b10ea"
down_revision = "1f5db5dfad80"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "tag",
        sa.Column("label", sa.String(length=40), nullable=False),
        sa.Column("color", sa.String(length=20), nullable=True),
        sa.PrimaryKeyConstraint("label"),
    )
    with op.batch_alter_table("tag", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_tag_color"), ["color"], unique=False)
        batch_op.create_index(batch_op.f("ix_tag_label"), ["label"], unique=False)

    op.create_table(
        "study_tag",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("tag_label", sa.String(length=40), nullable=False),
        sa.ForeignKeyConstraint(["study_id"], ["study.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_label"], ["tag.label"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("study_id", "tag_label"),
    )
    with op.batch_alter_table("study_tag", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_study_tag_study_id"), ["study_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_study_tag_tag_label"), ["tag_label"], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("study_tag", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_study_tag_tag_label"))
        batch_op.drop_index(batch_op.f("ix_study_tag_study_id"))

    op.drop_table("study_tag")
    with op.batch_alter_table("tag", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_tag_label"))
        batch_op.drop_index(batch_op.f("ix_tag_color"))

    op.drop_table("tag")
    # ### end Alembic commands ###
