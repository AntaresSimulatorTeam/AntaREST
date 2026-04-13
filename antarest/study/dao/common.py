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
from typing import NewType, TypeAlias

from antarest.study.business.model.scenario_builder_model import ConstraintId

# TODO: It would be better to :
#  - Use `NewType` instead of `TypeAlias`
#  - Move these definitions inside their corresponding models.

AreaId: TypeAlias = str
ThermalId: TypeAlias = str
RenewableId: TypeAlias = str
SeriesId: TypeAlias = str

ThermalSeriesMapping: TypeAlias = dict[AreaId, dict[ThermalId, SeriesId]]
RenewableSeriesMapping: TypeAlias = dict[AreaId, dict[RenewableId, SeriesId]]
AreaSeriesMapping: TypeAlias = dict[AreaId, SeriesId]
LinkSeriesMapping: TypeAlias = dict[tuple[AreaId, AreaId], SeriesId]
BindingConstraintSeriesMapping: TypeAlias = dict[ConstraintId, SeriesId]
