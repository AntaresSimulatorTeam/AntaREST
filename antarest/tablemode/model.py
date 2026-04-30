# Copyright (c) 2026, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

from enum import StrEnum
from uuid import UUID

from pydantic import model_validator
from sqlalchemy import ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from antarest.core.persistence import Base
from antarest.core.serde import AntaresBaseModel


class TableType(StrEnum):
    """
    Table types.

    This enum is used to define the different types of tables that can be created
    by the user to leverage the editing capabilities of multiple objects at once.

    Attributes:
        AREA: Area table.
        LINK: Link table.
        THERMAL: Thermal clusters table.
        RENEWABLE: Renewable clusters table.
        ST_STORAGE: Short-Term Storages table.
        BINDING_CONSTRAINT: Binding constraints table.
    """

    AREA = "areas"
    LINK = "links"
    THERMAL = "thermals"
    RENEWABLE = "renewables"
    # Avoid "storages" because we may have "lt-storages" (long-term storages) in the future
    ST_STORAGE = "st-storages"
    # Avoid "constraints" because we may have other kinds of constraints in the future
    BINDING_CONSTRAINT = "binding-constraints"
    ST_STORAGE_ADDITIONAL_CONSTRAINTS = "st-storages-additional-constraints"


class AreaColumn(StrEnum):
    NON_DISPATCHABLE_POWER = "nonDispatchPower"
    DISPATCHABLE_HYDRO_POWER = "dispatchHydroPower"
    OTHER_DISPATCHABLE_POWER = "otherDispatchPower"
    ENERGY_COST_UNSUPPLIED = "energyCostUnsupplied"
    SPREAD_UNSUPPLIED_ENERGY_COST = "spreadUnsuppliedEnergyCost"
    ENERGY_COST_SPILLED = "energyCostSpilled"
    SPREAD_SPILLED_ENERGY_COST = "spreadSpilledEnergyCost"
    FILTER_SYNTHESIS = "filterSynthesis"
    FILTER_BY_YEAR = "filterByYear"
    # Since v8.3
    ADEQUACY_PATCH_MODE = "adequacyPatchMode"


class LinkColumn(StrEnum):
    HURDLES_COST = "hurdlesCost"
    LOOP_FLOW = "loopFlow"
    USE_PHASE_SHIFTER = "usePhaseShifter"
    TRANSMISSION_CAPACITIES = "transmissionCapacities"
    ASSET_TYPE = "assetType"
    LINK_STYLE = "linkStyle"
    LINK_WIDTH = "linkWidth"
    COMMENTS = "comments"
    DISPLAY_COMMENTS = "displayComments"
    FILTER_SYNTHESIS = "filterSynthesis"
    FILTER_YEAR_BY_YEAR = "filterYearByYear"


class ThermalColumn(StrEnum):
    GROUP = "group"
    ENABLED = "enabled"
    UNIT_COUNT = "unitCount"
    NOMINAL_CAPACITY = "nominalCapacity"
    GEN_TS = "genTs"
    MIN_STABLE_POWER = "minStablePower"
    MIN_UP_TIME = "minUpTime"
    MIN_DOWN_TIME = "minDownTime"
    MUST_RUN = "mustRun"
    SPINNING = "spinning"
    VOLATILITY_FORCED = "volatilityForced"
    VOLATILITY_PLANNED = "volatilityPlanned"
    LAW_FORCED = "lawForced"
    LAW_PLANNED = "lawPlanned"
    MARGINAL_COST = "marginalCost"
    SPREAD_COST = "spreadCost"
    FIXED_COST = "fixedCost"
    STARTUP_COST = "startupCost"
    MARKET_BID_COST = "marketBidCost"
    CO2 = "co2"
    # Since v8.6
    NH3 = "nh3"
    SO2 = "so2"
    NOX = "nox"
    PM25 = "pm25"
    PM5 = "pm5"
    PM10 = "pm10"
    NMVOC = "nmvoc"
    OP1 = "op1"
    OP2 = "op2"
    OP3 = "op3"
    OP4 = "op4"
    OP5 = "op5"
    # Since v8.7
    COST_GENERATION = "costGeneration"
    EFFICIENCY = "efficiency"
    VARIABLE_OM_COST = "variableOMCost"


class RenewableColumn(StrEnum):
    GROUP = "group"
    ENABLED = "enabled"
    TS_INTERPRETATION = "tsInterpretation"
    UNIT_COUNT = "unitCount"
    NOMINAL_CAPACITY = "nominalCapacity"


class STStorageColumn(StrEnum):
    GROUP = "group"
    INJECTION_NOMINAL_CAPACITY = "injectionNominalCapacity"
    WITHDRAWAL_NOMINAL_CAPACITY = "withdrawalNominalCapacity"
    RESERVOIR_CAPACITY = "reservoirCapacity"
    EFFICIENCY = "efficiency"
    INITIAL_LEVEL = "initialLevel"
    INITIAL_LEVEL_OPTIM = "initialLevelOptim"
    ENABLED = "enabled"
    EFFICIENCY_WITHDRAWAL = "efficiencyWithdrawal"
    PENALIZE_VARIATION_INJECTION = "penalizeVariationInjection"
    PENALIZE_VARIATION_WITHDRAWAL = "penalizeVariationWithdrawal"


class BindingConstraintColumn(StrEnum):
    ENABLED = "enabled"
    TIME_STEP = "timeStep"
    OPERATOR = "operator"
    COMMENTS = "comments"
    # Since v8.3
    FILTER_SYNTHESIS = "filterSynthesis"
    FILTER_YEAR_BY_YEAR = "filterYearByYear"
    # Since v8.7
    GROUP = "group"


class STStorageAdditionalConstraintsColumn(StrEnum):
    # Since v9.2
    VARIABLE = "variable"
    OPERATOR = "operator"
    ENABLED = "enabled"


TableColumn = AreaColumn | LinkColumn | ThermalColumn | RenewableColumn | STStorageColumn | BindingConstraintColumn


# Mapping of TableType to their corresponding column enums
TABLE_TYPE_COLUMN_MAPPING: dict[TableType, type[StrEnum]] = {
    TableType.AREA: AreaColumn,
    TableType.LINK: LinkColumn,
    TableType.THERMAL: ThermalColumn,
    TableType.RENEWABLE: RenewableColumn,
    TableType.ST_STORAGE: STStorageColumn,
    TableType.BINDING_CONSTRAINT: BindingConstraintColumn,
    TableType.ST_STORAGE_ADDITIONAL_CONSTRAINTS: STStorageAdditionalConstraintsColumn,
}


class StorageAdditionalConstraintColumn(StrEnum):
    VARIABLE = "variable"
    OPERATOR = "operator"
    ENABLED = "enabled"


class TableMode(Base):
    __tablename__ = "tablemode"

    table_id: Mapped[UUID] = mapped_column(Uuid(), primary_key=True, nullable=False)
    table_name: Mapped[str] = mapped_column(String(255), nullable=False)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("identities.id", name="fk_user_id", ondelete="CASCADE"), nullable=False, index=True
    )
    table_type: Mapped[TableType] = mapped_column(String(255), nullable=False)
    table_columns: Mapped[str] = mapped_column(nullable=False)

    def to_dto(self) -> "TableModeDTO":
        return TableModeDTO(
            table_id=self.table_id,
            table_name=self.table_name,
            table_type=self.table_type,
            table_columns=self.table_columns.split(","),
        )


class TableModeDTO(AntaresBaseModel, extra="forbid"):
    table_id: UUID
    table_name: str
    table_type: TableType
    table_columns: list[TableColumn]

    @model_validator(mode="after")
    def check_coherence(self) -> "TableModeDTO":
        # checking the table columns match the table_type
        if self.table_type in TABLE_TYPE_COLUMN_MAPPING:
            columns = TABLE_TYPE_COLUMN_MAPPING[self.table_type]
            valid_values = [column.value for column in columns]
            for column in self.table_columns:
                if column not in valid_values:
                    raise ValueError(f"Invalid column {column} for table type {self.table_type}")
        return self
