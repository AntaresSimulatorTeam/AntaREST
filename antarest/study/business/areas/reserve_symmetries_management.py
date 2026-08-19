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
from antarest.study.business.model.reserve_certification_model import StorageId
from antarest.study.business.model.reserve_symmetries_model import ReserveSymmetries
from antarest.study.business.study_interface import StudyInterface
from antarest.study.dao.common import ThermalId
from antarest.study.storage.variantstudy.model.command.replace_st_storage_reserve_symmetries import (
    ReplaceStStorageReserveSymmetries,
)
from antarest.study.storage.variantstudy.model.command.replace_thermal_reserve_symmetries import (
    ReplaceThermalReserveSymmetries,
)
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class ReserveSymmetriesManager:
    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_thermal_symmetries(self, study: StudyInterface, area_id: str) -> dict[ThermalId, ReserveSymmetries]:
        return study.get_study_dao().get_thermal_reserve_symmetries(area_id)

    def set_thermal_symmetries(
        self, study: StudyInterface, area_id: str, data: dict[ThermalId, ReserveSymmetries]
    ) -> dict[ThermalId, ReserveSymmetries]:
        command = ReplaceThermalReserveSymmetries(
            area_id=area_id,
            symmetries=data,
            command_context=self._command_context,
            study_version=study.version,
        )
        study.add_commands([command])
        return data

    def get_st_storage_symmetries(self, study: StudyInterface, area_id: str) -> dict[StorageId, ReserveSymmetries]:
        return study.get_study_dao().get_st_storage_reserve_symmetries(area_id)

    def set_st_storage_symmetries(
        self, study: StudyInterface, area_id: str, data: dict[StorageId, ReserveSymmetries]
    ) -> dict[StorageId, ReserveSymmetries]:
        command = ReplaceStStorageReserveSymmetries(
            area_id=area_id,
            symmetries=data,
            command_context=self._command_context,
            study_version=study.version,
        )
        study.add_commands([command])
        return data
