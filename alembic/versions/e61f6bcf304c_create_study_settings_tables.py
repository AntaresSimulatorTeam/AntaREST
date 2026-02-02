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

def downgrade():
    pass
