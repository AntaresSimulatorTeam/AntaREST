"""add_library_id_in_models_primary_keys

Revision ID: bb26e0cd63ea
Revises: 3302075bbdfd
Create Date: 2026-10-01 08:47:28.807356

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = 'bb26e0cd63ea'
down_revision = '3302075bbdfd'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("gems_models_ports") as batch_op:
        batch_op.drop_constraint("pk_gems_models_ports", type_="primary")
        batch_op.create_primary_key("pk_gems_models_ports", ["study_data_id", "library_id", "model_id", "port_id"])

    with op.batch_alter_table("gems_models_parameters") as batch_op:
        batch_op.drop_constraint("pk_gems_models_parameters", type_="primary")
        batch_op.create_primary_key(
            "pk_gems_models_parameters", ["study_data_id", "library_id", "model_id", "parameter_id"]
        )


def downgrade():
    with op.batch_alter_table("gems_models_parameters") as batch_op:
        batch_op.drop_constraint("pk_gems_models_parameters", type_="primary")
        batch_op.create_primary_key("pk_gems_models_parameters", ["study_data_id", "model_id", "parameter_id"])

    with op.batch_alter_table("gems_models_ports") as batch_op:
        batch_op.drop_constraint("pk_gems_models_ports", type_="primary")
        batch_op.create_primary_key("pk_gems_models_ports", ["study_data_id", "model_id", "port_id"])

