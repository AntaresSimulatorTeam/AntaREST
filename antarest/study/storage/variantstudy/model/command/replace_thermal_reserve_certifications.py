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


from typing import Any, Self

from pydantic import model_validator
from typing_extensions import override

from antarest.core.exceptions import InvalidFieldForVersionError
from antarest.study.business.model.thermal_reserve_certification_model import ThermalReserveCertificationMapping
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.dao.common import AreaId
from antarest.study.model import (
    STUDY_VERSION_10_0,
)
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
    CommandOutput,
    command_succeeded,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class ReplaceThermalReserveCertifications(ICommand):
    """
    Command used to replace reserve certifications for a given area
    """

    command_name: CommandName = CommandName.REPLACE_THERMAL_RESERVE_CERTIFICATIONS

    # Command parameters
    # ==================

    area_id: AreaId
    certifications: ThermalReserveCertificationMapping

    @model_validator(mode="after")
    def _validate_version(self) -> Self:
        if self.study_version < STUDY_VERSION_10_0:
            msg = "Thermal cluster reserve certifications are not valid for study version before 10.0"
            raise InvalidFieldForVersionError(msg)

        return self

    @override
    def _apply_dao(
        self, study_data: StudyDao, listener: ICommandListener | None = None
    ) -> CommandOutput[ThermalReserveCertificationMapping]:
        study_data.save_thermal_reserve_certifications({self.area_id: self.certifications})

        msg = f"Reserve certifications in area '{self.area_id}' replaced successfully."
        return command_succeeded(msg, result=self.certifications)

    @override
    def to_dto(self) -> CommandDTO:
        args: dict[str, Any] = {}
        for reserve_id, thermal_dict in self.certifications.items():
            args["reserve_id"] = {}
            for thermal_id, certification in thermal_dict.items():
                args.setdefault(reserve_id, {})[thermal_id] = certification.model_dump(mode="json")

        return CommandDTO(
            action=CommandName.REPLACE_THERMAL_RESERVE_CERTIFICATIONS.value,
            args={"area_id": self.area_id, "certifications": args},
            study_version=self.study_version,
        )
