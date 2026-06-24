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


from antarest.core.exceptions import InvalidFieldForVersionError, AreaNotFound
from antarest.study.business.model.reserve_definition_model import ReserveDefinitionId
from antarest.study.business.model.thermal_reserve_certification_model import (
    ThermalReserveCertification,
    ThermalReserveCertificationCreation,
    create_thermal_reserve_certification, ThermalReserveCertificationUpdate, ThermalReserveCertificationUpdates,
    update_thermal_reserve_certification,
)
from antarest.study.dao.common import AreaId, ThermalId, ThermalReserveCertificationsMapping

from typing import Self, Any

from pydantic import model_validator
from typing_extensions import override

from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.model import (
    STUDY_VERSION_10_0,
)
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
    CommandOutput,
    command_failed,
    command_succeeded,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class UpdateThermalReserveCertifications(ICommand):
    """
    Command used to create a new thermal reserve certification in the study.
    """
    command_name: CommandName = CommandName.UPDATE_THERMAL_RESERVE_CERTIFICATIONS

    # Command parameters
    # ==================

    parameters: ThermalReserveCertificationUpdates

    @model_validator(mode="after")
    def _validate_version(self) -> Self:
        if self.study_version < STUDY_VERSION_10_0:
            msg = "Thermal cluster reserve certifications are not valid for study version before 10.0"
            raise InvalidFieldForVersionError(msg)
        return self

    @override
    def _apply_dao(self, study_data: StudyDao, listener: ICommandListener | None = None) -> CommandOutput[ThermalReserveCertificationsMapping]:
        """
        We validate ALL objects before saving them.
        This way, if some data is invalid, we're not modifying the study partially only.
        """
        memory_mapping: ThermalReserveCertificationsMapping = {}

        for area_id, thermal_dict in self.parameters.items():
            memory_mapping[area_id] = {}
            for thermal_id, reserves_dict in thermal_dict.items():
                memory_mapping[area_id][thermal_id] = {}
                all_certifications = study_data.get_all_thermal_reserve_certifications_for_cluster(area_id, thermal_id)
                for reserve_id, certification_update in reserves_dict.items():
                    if reserve_id not in all_certifications:
                        return command_failed(f"Reserve certification '{reserve_id}' does not exist for area '{area_id}' and thermal '{thermal_id}'")

                    certification = update_thermal_reserve_certification(all_certifications[reserve_id], certification_update)
                    memory_mapping[area_id][thermal_id][reserve_id] = certification


        study_data.save_thermal_reserve_certifications(memory_mapping)

        return command_succeeded("All thermal certifications updated", result=memory_mapping)

    @override
    def to_dto(self) -> CommandDTO:
        args: dict[str, dict[str, Any]] = {}

        for area_id, thermal_dict in self.parameters.items():
            args[area_id] = {}
            for thermal_id, reserves_dict in thermal_dict.items():
                args[area_id][thermal_id] = {}
                for reserve_id, certification in reserves_dict.items():
                    args[area_id][thermal_id][reserve_id] = certification.model_dump(mode="json", exclude_none=True)

        return CommandDTO(
            action=CommandName.UPDATE_THERMAL_RESERVE_CERTIFICATIONS.value,
            args=args,
            study_version=self.study_version        )
