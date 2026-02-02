"""create_study_settings_tables

Revision ID: e61f6bcf304c
Revises: 6a6d36e3c6ed
Create Date: 2026-02-02 14:49:58.622967

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e61f6bcf304c'
down_revision = '6a6d36e3c6ed'
branch_labels = None
depends_on = None


def upgrade():
    # 1- Declare the Enums
    simulation_mode_enum = sa.Enum('Economy', 'Adequacy', 'Expansion', name="simulationmode")
    month_enum = sa.Enum('january', 'february', 'march', 'april', 'may', 'june', 'july', "august", "september", "october", "november", "december", name="month")
    weekday_enum = sa.Enum('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', "Saturday", "Sunday", name="weekday")
    price_taking_order_enum = sa.Enum("DENS", 'Load', name="pricetakingorder")
    building_mode_enum = sa.Enum("Automatic", 'Custom', "Derated", name="buildingmode")
    unfeasible_problem_behavior_enum = sa.Enum("warning-dry", "warning-verbose", "error-dry", "error-verbose", name="unfeasibleproblembehavior")
    simplex_optimization_range_enum = sa.Enum("day", "week", name="simplexoptimizationrange")
    hydro_pmax_enum = sa.Enum("daily", "hourly", name="hydropmax")
    power_fluctuation_enum = sa.Enum("free modulations", "minimize excursions", "minimize ramping", name="powerfluctuation")
    shedding_policy_enum = sa.Enum("shave peaks", "accurate shave peaks", "minimize duration", name="sheddingpolicy")
    reserve_management_enum = sa.Enum("global", name="reservemanagement")
    unit_commitment_mode_enum = sa.Enum("fast", "milp", "accurate", name="unitcommitmentmode")
    simulation_core_enum = sa.Enum("minimum", "low", "medium", "high", "maximum", name="simulationcore")
    renewable_generation_modeling_enum = sa.Enum("aggregated", "clusters", name="renewablegenerationmodeling")
    initial_reservoir_level_enum = sa.Enum("cold start", "hot start", name="initialreservoirlevel")
    hydro_heuristic_policy_enum = sa.Enum("accommodate rule curves", "maximize generation", name="hydroheuristicpolicy")
    hydro_pricing_mode_enum = sa.Enum("fast", "accurate", name="hydropricingmode")

    ##########################
    # 2 - Create the tables
    ##########################

    # GeneralConfig
    op.create_table("general_config",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("mode", simulation_mode_enum, nullable=False),
        sa.Column("first_day", sa.Integer(), nullable=False),
        sa.Column("last_day", sa.Integer(), nullable=False),
        sa.Column("horizon", sa.String(), nullable=False),
        sa.Column("first_month", month_enum, nullable=False),
        sa.Column("first_week_day", weekday_enum, nullable=False),
        sa.Column("first_january", weekday_enum, nullable=False),
        sa.Column("leap_year", sa.Boolean(), nullable=False),
        sa.Column("nb_years", sa.Integer(), nullable=False),
        sa.Column("building_mode", building_mode_enum, nullable=False),
        sa.Column("selection_mode", sa.Boolean(), nullable=False),
        sa.Column("year_by_year", sa.Boolean(), nullable=False),
        sa.Column("simulation_synthesis", sa.Boolean(), nullable=False),
        sa.Column("mc_scenario", sa.Boolean(), nullable=False),
        sa.Column("filtering", sa.Boolean(), nullable=True),
        sa.Column("geographic_trimming", sa.Boolean(), nullable=True),
        sa.Column("thematic_trimming", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(["study_id"],["study.id"], name="fk_general_config_study_id", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("study_id", name=op.f("pk_general_config"))
    )

    # AdvancedParameters
    op.create_table("advanced_parameters",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("accuracy_on_correlation", sa.String(), nullable=False),
        sa.Column("power_fluctuations", power_fluctuation_enum, nullable=False),
        sa.Column("shedding_policy", shedding_policy_enum, nullable=False),
        sa.Column("hydro_pricing_mode", hydro_pricing_mode_enum, nullable=False),
        sa.Column("hydro_heuristic_policy", hydro_heuristic_policy_enum, nullable=False),
        sa.Column("unit_commitment_mode", unit_commitment_mode_enum, nullable=False),
        sa.Column("number_of_cores_mode", simulation_core_enum, nullable=False),
        sa.Column("day_ahead_reserve_management", reserve_management_enum, nullable=False),
        sa.Column("renewable_generation_modelling", renewable_generation_modeling_enum, nullable=False),
        sa.Column("seed_tsgen_wind", sa.Integer(), nullable=False),
        sa.Column("seed_tsgen_load", sa.Integer(), nullable=False),
        sa.Column("seed_tsgen_hydro", sa.Integer(), nullable=False),
        sa.Column("seed_tsgen_thermal", sa.Integer(), nullable=False),
        sa.Column("seed_tsgen_solar", sa.Integer(), nullable=False),
        sa.Column("seed_tsnumbers", sa.Integer(), nullable=False),
        sa.Column("seed_unsupplied_energy_costs", sa.Integer(), nullable=False),
        sa.Column("seed_spilled_energy_costs", sa.Integer(), nullable=False),
        sa.Column("seed_thermal_costs", sa.Integer(), nullable=False),
        sa.Column("seed_hydro_costs", sa.Integer(), nullable=False),
        sa.Column("seed_initial_reservoir_levels", sa.Integer(), nullable=False),
        sa.Column("initial_reservoir_levels", initial_reservoir_level_enum, nullable=True),
        sa.Column("accurate_shave_peaks_include_short_term_storage", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(["study_id"], ["study.id"], name="fk_advanced_parameters_study_id", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("study_id", name=op.f("pk_advanced_parameters"))
    )

    # AdequacyPatchParameters
    op.create_table("adequacy_patch_parameters",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("enable_adequacy_patch", sa.Boolean(), nullable=False),
        sa.Column("ntc_from_physical_areas_out_to_physical_areas_in_adequacy_patch", sa.Boolean(), nullable=False),
        sa.Column("price_taking_order", price_taking_order_enum, nullable=True),
        sa.Column("include_hurdle_cost_csr", sa.Boolean(), nullable=True),
        sa.Column("check_csr_cost_function", sa.Boolean(), nullable=True),
        sa.Column("threshold_initiate_curtailment_sharing_rule", sa.Float(), nullable=True),
        sa.Column("threshold_display_local_matching_rule_violations", sa.Float(), nullable=True),
        sa.Column("threshold_csr_variable_bounds_relaxation", sa.Integer(), nullable=True),
        sa.Column("ntc_between_physical_areas_out_adequacy_patch", sa.Boolean(), nullable=True),
        sa.Column("redispatch", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(["study_id"], ["study.id"], name="fk_adequacy_patch_parameters_study_id", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("study_id", name=op.f("pk_adequacy_patch_parameters"))
    )

    # CompatibilityParameters
    op.create_table("compatibility_parameters",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("hydro_pmax", hydro_pmax_enum, nullable=True),
        sa.ForeignKeyConstraint(["study_id"], ["study.id"], name="fk_compatibility_parameters_study_id", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("study_id", name=op.f("pk_compatibility_parameters"))
    )

    # OptimizationPreferences
    op.create_table("optimization_preferences",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("binding_constraints", sa.Boolean(), nullable=False),
        sa.Column("hurdle_costs", sa.Boolean(), nullable=False),
        sa.Column("transmission_capacities", sa.String(), nullable=False),
        sa.Column("thermal_clusters_min_stable_power", sa.Boolean(), nullable=False),
        sa.Column("thermal_clusters_min_ud_time", sa.Boolean(), nullable=False),
        sa.Column("day_ahead_reserve", sa.Boolean(), nullable=False),
        sa.Column("primary_reserve", sa.Boolean(), nullable=False),
        sa.Column("strategic_reserve", sa.Boolean(), nullable=False),
        sa.Column("spinning_reserve", sa.Boolean(), nullable=False),
        sa.Column("export_mps", sa.String(), nullable=False),
        sa.Column("unfeasible_problem_behavior", unfeasible_problem_behavior_enum, nullable=False),
        sa.Column("simplex_optimization_range", simplex_optimization_range_enum, nullable=False),
        sa.ForeignKeyConstraint(["study_id"], ["study.id"], name="fk_optimization_preferences_study_id", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("study_id", name=op.f("pk_optimization_preferences"))
    )

    # TimeSeries
    op.create_table("timeseries_config",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("thermal_number", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["study_id"], ["study.id"], name="fk_timeseries_config_study_id", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("study_id", name=op.f("pk_timeseries_config"))
    )

    # Playlist
    op.create_table("playlist",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("years", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["study_id"], ["study.id"], name="fk_playlist_study_id", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("study_id", name=op.f("pk_playlist"))
    )

def downgrade():
    # Drop table
    op.drop_table("general_config")
    op.drop_table("advanced_parameters")
    op.drop_table("adequacy_patch_parameters")
    op.drop_table("compatibility_parameters")
    op.drop_table("optimization_preferences")
    op.drop_table("timeseries_config")
    op.drop_table("playlist")

    # Drop enum type (PostgreSQL only)
    if op.get_context().dialect.name == "postgresql":
        sa.Enum(name="simulationmode").drop(op.get_bind(), checkfirst=True)
        sa.Enum(name="month").drop(op.get_bind(), checkfirst=True)
        sa.Enum(name="weekday").drop(op.get_bind(), checkfirst=True)
        sa.Enum(name="pricetakingorder").drop(op.get_bind(), checkfirst=True)
        sa.Enum(name="buildingmode").drop(op.get_bind(), checkfirst=True)
        sa.Enum(name="unfeasibleproblembehavior").drop(op.get_bind(), checkfirst=True)
        sa.Enum(name="simplexoptimizationrange").drop(op.get_bind(), checkfirst=True)
        sa.Enum(name="hydropmax").drop(op.get_bind(), checkfirst=True)
        sa.Enum(name="powerfluctuation").drop(op.get_bind(), checkfirst=True)
        sa.Enum(name="sheddingpolicy").drop(op.get_bind(), checkfirst=True)
        sa.Enum(name="reservemanagement").drop(op.get_bind(), checkfirst=True)
        sa.Enum(name="unitcommitmentmode").drop(op.get_bind(), checkfirst=True)
        sa.Enum(name="simulationcore").drop(op.get_bind(), checkfirst=True)
        sa.Enum(name="renewablegenerationmodeling").drop(op.get_bind(), checkfirst=True)
        sa.Enum(name="initialreservoirlevel").drop(op.get_bind(), checkfirst=True)
        sa.Enum(name="hydroheuristicpolicy").drop(op.get_bind(), checkfirst=True)
        sa.Enum(name="hydropricingmode").drop(op.get_bind(), checkfirst=True)
