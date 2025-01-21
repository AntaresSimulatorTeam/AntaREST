# Copyright (c) 2025, RTE (https://www.rte-france.com)
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
import typing as t

from typing_extensions import override

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.study.business.model.link_model import LinkInternal, LinkTsGeneration
from antarest.study.model import LinksParametersTsGeneration
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.create_link import AbstractLinkCommand
from antarest.study.storage.variantstudy.model.command.icommand import ICommand, OutputTuple
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class UpdateLink(AbstractLinkCommand):
    """
    Command used to update a link between two areas.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_LINK
    version: int = 1

    @override
    def _apply_config(self, study_data: FileStudyTreeConfig) -> OutputTuple:
        return (
            CommandOutput(
                status=True,
                message=f"Link between '{self.area1}' and '{self.area2}' updated",
            ),
            {},
        )

    @override
    def _apply(self, study_data: FileStudy, listener: t.Optional[ICommandListener] = None) -> CommandOutput:
        version = study_data.config.version

        properties = study_data.tree.get(["input", "links", self.area1, "properties", self.area2])

        internal_link = LinkInternal.model_validate(self.parameters)

        # Updates ini properties
        new_ini_properties = internal_link.model_dump(include=self.parameters, by_alias=True)
        properties.update(new_ini_properties)
        study_data.tree.save(properties, ["input", "links", self.area1, "properties", self.area2])

        output, _ = self._apply_config(study_data.config)

        # Updates DB properties
        includes = set(LinkTsGeneration.model_fields.keys())
        db_properties = LinkTsGeneration.model_validate(internal_link.model_dump(mode="json", include=includes))

        with db():
            study_id = study_data.config.study_id
            new_parameters = LinksParametersTsGeneration(
                study_id=study_id,
                area_from=self.area1,
                area_to=self.area2,
                unit_count=db_properties.unit_count,
                nominal_capacity=db_properties.nominal_capacity,
                law_planned=db_properties.law_planned,
                law_forced=db_properties.law_forced,
                volatility_planned=db_properties.volatility_planned,
                volatility_forced=db_properties.volatility_forced,
                force_no_generation=db_properties.force_no_generation,
            )
            db.session.merge(new_parameters)
            db.session.commit()

        # Updates matrices
        if self.series:
            self.save_series(self.area1, self.area2, study_data, version)

        if self.direct:
            self.save_direct(self.area1, self.area2, study_data, version)

        if self.indirect:
            self.save_indirect(self.area1, self.area2, study_data, version)

        return output

    @override
    def to_dto(self) -> CommandDTO:
        return super().to_dto()

    @override
    def match_signature(self) -> str:
        return super().match_signature()

    @override
    def _create_diff(self, other: "ICommand") -> t.List["ICommand"]:
        return super()._create_diff(other)

    @override
    def get_inner_matrices(self) -> t.List[str]:
        return super().get_inner_matrices()
