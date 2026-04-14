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
from typing import TypeAlias

from antarest.study.business.model.binding_constraint_model import ConstraintId

# TODO: It would be better to :
#  - Use `NewType` instead of `TypeAlias`
#  - Move these definitions inside their corresponding models.

AreaId: TypeAlias = str
ThermalId: TypeAlias = str
RenewableId: TypeAlias = str
StStorageId: TypeAlias = str
SeriesId: TypeAlias = str
XpansionFileName: TypeAlias = str

ThermalSeriesMapping: TypeAlias = dict[AreaId, dict[ThermalId, SeriesId]]
RenewableSeriesMapping: TypeAlias = dict[AreaId, dict[RenewableId, SeriesId]]
StStorageSeriesMapping: TypeAlias = dict[AreaId, dict[StStorageId, SeriesId]]
AreaSeriesMapping: TypeAlias = dict[AreaId, SeriesId]
LinkSeriesMapping: TypeAlias = dict[tuple[AreaId, AreaId], SeriesId]
BindingConstraintSeriesMapping: TypeAlias = dict[ConstraintId, SeriesId]
XpansionWeightsMapping: TypeAlias = dict[XpansionFileName, SeriesId]
XpansionCapacitiesMapping: TypeAlias = dict[XpansionFileName, SeriesId]
XpansionConstraintsMapping: TypeAlias = dict[XpansionFileName, bytes]
