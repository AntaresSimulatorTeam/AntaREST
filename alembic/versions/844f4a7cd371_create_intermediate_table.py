"""create_intermediate_table

Revision ID: 844f4a7cd371
Revises: 4121d3b48393
Create Date: 2026-05-28 16:27:08.165716

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '844f4a7cd371'
down_revision = '4121d3b48393'
branch_labels = None
depends_on = None


TABLE_NAME = 'study_data_container'

DAO_TABLES = [
    ("area", ""),
    ("area_ui", ""),
    ("load", ""),
    ("solar", ""),
    ("wind", ""),
    ("reserves", ""),
    ("misc_gen", ""),
    ("reserves_global_parameters", ""),
    ("binding_constraint", ""),
    ("binding_constraint_link_term", ""),
    ("binding_constraint_cluster_term", ""),
    ("binding_constraint_values_matrix", ""),
    ("binding_constraint_lt_matrix", ""),
    ("binding_constraint_gt_matrix", ""),
    ("binding_constraint_eq_matrix", ""),
    ("comments", ""),
    ("district", ""),
    ("hydro_management", ""),
    ("hydro_inflow_structure", ""),
    ("hydro_allocation", ""),
    ("hydro_correlation", ""),
    ("hydro_maxpower", ""),
    ("hydro_reservoir", ""),
    ("hydro_energy", ""),
    ("hydro_run_of_river", ""),
    ("hydro_modulation", ""),
    ("hydro_credit_modulations", ""),
    ("hydro_inflow_pattern", ""),
    ("hydro_water_values", ""),
    ("hydro_mingen", ""),
    ("hydro_max_hourly_gen_power", ""),
    ("hydro_max_hourly_pump_power", ""),
    ("hydro_max_daily_gen_energy", ""),
    ("hydro_max_daily_pump_energy", ""),
    ("layer", ""),
    ("link", ""),
    ("link_series", ""),
    ("link_direct_capacity", ""),
    ("link_indirect_capacity", ""),
    ("renewable_cluster", ""),
    ("renewable_series", ""),
    ("reserve_definition", ""),
    ("reserve_need_matrix", ""),
    ("scenario_load", ""),
    ("scenario_hydro", ""),
    ("scenario_wind", ""),
    ("scenario_solar", ""),
    ("scenario_hydro_initial_level", ""),
    ("scenario_hydro_final_level", ""),
    ("scenario_hydro_generation_power", ""),
    ("scenario_ntc", ""),
    ("scenario_binding_constraints", ""),
    ("scenario_thermal", ""),
    ("scenario_renewable", ""),
    ("scenario_storage_inflows", ""),
    ("scenario_storage_constraints", ""),
    ("general_config", ""),
    ("advanced_parameters", ""),
    ("adequacy_patch_parameters", ""),
    ("compatibility_parameters", ""),
    ("optimization_preferences", ""),
    ("timeseries_config", ""),
    ("playlist", ""),
    ("st_storage", ""),
    ("st_storage_pmax_injection", ""),
    ("st_storage_pmax_withdrawal", ""),
    ("st_storage_lower_rule_curve", ""),
    ("st_storage_upper_rule_curve", ""),
    ("st_storage_inflows", ""),
    ("st_storage_cost_injection", ""),
    ("st_storage_cost_withdrawal", ""),
    ("st_storage_cost_level", ""),
    ("st_storage_cost_variation_injection", ""),
    ("st_storage_cost_variation_withdrawal", ""),
    ("st_storage_additional_constraint", ""),
    ("st_storage_additional_constraint_matrix", ""),
    ("thematic_trimming", ""),
    ("thermal_cluster", ""),
    ("thermal_prepro", ""),
    ("thermal_modulation", ""),
    ("thermal_series", ""),
    ("thermal_fuel_cost", ""),
    ("thermal_co2_cost", ""),
    ("user_resources", ""),
    ("xpansion_settings", ""),
    ("xpansion_sensitivity_projection", ""),
    ("xpansion_adequacy_criterion", ""),
    ("xpansion_adequacy_pattern", ""),
    ("xpansion_constraint", ""),
    ("xpansion_capacity", ""),
    ("xpansion_weight", "")
]

def upgrade():
    """
    Introduce an intermediate table between DAO and Study, useful for clearing variant snapshots.
    When doing so, we'll only have to flush this table and everything will be removed by cascade.
    """

    # Create the new intermediate table
    op.create_table(
        TABLE_NAME,
        sa.Column('study_id', sa.String(length=36), sa.ForeignKey('study.id'), nullable=False)
    )

    # For each DAO table that previously referenced study.id, we'll now use the `study_data_container` table
    for (table, foreign_key) in DAO_TABLES:
        op.drop_constraint(foreign_key, table, type_='foreignkey')
        op.create_foreign_key(foreign_key, table, TABLE_NAME,['study_id'], ['study_id'], ondelete="CASCADE")

def downgrade():
    for (table, foreign_key) in DAO_TABLES:
        op.drop_constraint(foreign_key, table, type_='foreignkey')
        op.create_foreign_key(foreign_key, table, "study",['study_id'], ['id'], ondelete="CASCADE")

    op.drop_table(TABLE_NAME)