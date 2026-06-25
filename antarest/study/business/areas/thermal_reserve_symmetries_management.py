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
from antarest.study.business.model.thermal_reserve_symmetries_model import ThermalReserveSymmetry
from antarest.study.business.study_interface import StudyInterface
from antarest.study.dao.common import ThermalId
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class ThermalReserveSymmetriesManager:
    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_symmetries(self, study: StudyInterface, area_id: str) -> dict[ThermalId, list[ThermalReserveSymmetry]]:
        raise NotImplementedError()

    def set_symmetries(
        self, study: StudyInterface, area_id: str, thermal_id: str, symmetries: list[ThermalReserveSymmetry]
    ) -> list[ThermalReserveSymmetry]:
        raise NotImplementedError()

    def delete_symmetries(
        self, study: StudyInterface, area_id: str, thermal_id: str, symmetries: list[ThermalReserveSymmetry]
    ) -> None:
        raise NotImplementedError()
