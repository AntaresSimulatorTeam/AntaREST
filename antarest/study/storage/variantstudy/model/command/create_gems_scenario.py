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
from typing import Self

from pydantic import model_validator
from typing_extensions import override

from antarest.study.business.model.gems.scenario_builder import GemsScBuilderMapping
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.model import STUDY_VERSION_10_2
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
    CommandOutput,
    command_succeeded,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class CreateGemsScenario(ICommand):
    """
    Command used to add a scenario inside the GEMS scenario-builder
    """

    command_name: CommandName = CommandName.CREATE_GEMS_SCENARIO

    scenario_name: str
    data: list[GemsScBuilderMapping]

    @model_validator(mode="after")
    def _validate_against_version(self) -> Self:
        if self.study_version < STUDY_VERSION_10_2:
            raise ValueError(f"GEMS scenario-builder is only available since version 10.2 and was {self.study_version}")
        return self

    @override
    def _apply_dao(
        self, study_dao: StudyDao, listener: ICommandListener | None = None
    ) -> CommandOutput[list[GemsScBuilderMapping]]:
        result = study_dao.save_scenario_inside_gems_scenario_builder(self.scenario_name, self.data)
        return command_succeeded(message=f"Gems scenario {self.scenario_name} added successfully", result=result)

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=self.command_name.value,
            args={"scenario_name": self.scenario_name, "data": [mapping.model_dump() for mapping in self.data]},
            study_version=self.study_version,
        )
