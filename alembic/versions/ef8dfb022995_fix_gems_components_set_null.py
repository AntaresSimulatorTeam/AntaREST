"""fix_gems_components_set_null

Revision ID: ef8dfb022995
Revises: 8f06c70c84eb
Create Date: 2026-11-10 10:56:22.277830

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'ef8dfb022995'
down_revision = '8f06c70c84eb'
branch_labels = None
depends_on = None


def upgrade():
    # Remove the "SET NULL" on delete behavior as it failed on PostgreSQL.
    # It tried to set null the `study_data_id` col too and there is no way currently to set null the `scenario_group` col only with Sqlite.
    with op.batch_alter_table('gems_components', schema=None) as batch_op:
        batch_op.drop_constraint("fk_gems_components_to_scenario_group", type_="foreignkey")
        batch_op.create_foreign_key(
            "fk_gems_components_to_scenario_group",
            "gems_scenario_builder",
            ["study_data_id", "scenario_group"],
            ["study_data_id", "scenario_group"],
            deferrable=True,
            initially="DEFERRED",
        )


def downgrade():
    with op.batch_alter_table('gems_components', schema=None) as batch_op:
        batch_op.drop_constraint("fk_gems_components_to_scenario_group", type_="foreignkey")
        batch_op.create_foreign_key(
            "fk_gems_components_to_scenario_group",
            "gems_scenario_builder",
            ["study_data_id", "scenario_group"],
            ["study_data_id", "scenario_group"],
            ondelete="SET NULL",
        )
