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
from typing import List, Optional

from typing_extensions import override

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.study.business.model.link_model import Area, LinkInternal, LinkTsGeneration
from antarest.study.model import STUDY_VERSION_8_2, LinksParametersTsGeneration
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.create_link import AbstractLinkCommand
from antarest.study.storage.variantstudy.model.command.icommand import OutputTuple
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
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        version = study_data.config.version
        area_from, area_to = sorted([self.area1, self.area2])

        internal_link = LinkInternal.model_validate(self.parameters)

        # Updates ini properties
        to_exclude = set(Area.model_fields.keys() | LinkTsGeneration.model_fields.keys())
        if version < STUDY_VERSION_8_2:
            to_exclude.update("filter-synthesis", "filter-year-by-year")
        new_ini_properties = internal_link.model_dump(by_alias=True, exclude=to_exclude, exclude_unset=True)
        if new_ini_properties:  # If no new INI properties were given we shouldn't update the INI file
            properties = study_data.tree.get(["input", "links", area_from, "properties", area_to])
            properties.update(new_ini_properties)
            study_data.tree.save(properties, ["input", "links", area_from, "properties", area_to])

        output, _ = self._apply_config(study_data.config)

        # Updates DB properties
        includes = set(LinkTsGeneration.model_fields.keys())
        db_properties_json = internal_link.model_dump(mode="json", include=includes, exclude_unset=True)
        if db_properties_json:  # If no new DB properties were given we shouldn't update the DB
            study_id = study_data.config.study_id
            with db():
                old_parameters = (
                    db.session.query(LinksParametersTsGeneration)
                    .filter_by(study_id=study_id, area_from=area_from, area_to=area_to)
                    .first()
                )
                if not old_parameters:
                    db_properties = LinkTsGeneration.model_validate(db_properties_json)
                    new_parameters = db_properties.to_db_model(study_id, area_from, area_to)
                else:
                    old_props = LinkTsGeneration.from_db_model(old_parameters).model_dump(mode="json")
                    old_props.update(db_properties_json)
                    new_parameters = LinkTsGeneration.model_validate(old_props).to_db_model(
                        study_id, area_from, area_to
                    )
                    # We should keep the same matrices
                    new_parameters.modulation = old_parameters.modulation
                    new_parameters.project = old_parameters.prepro
                    db.session.delete(old_parameters)
                db.session.add(new_parameters)
                db.session.commit()

        # Updates matrices
        if self.series:
            self.save_series(area_from, area_to, study_data, version)

        if self.direct:
            self.save_direct(area_from, area_to, study_data, version)

        if self.indirect:
            self.save_indirect(area_from, area_to, study_data, version)

        return output

    @override
    def to_dto(self) -> CommandDTO:
        return super().to_dto()

    @override
    def get_inner_matrices(self) -> List[str]:
        return super().get_inner_matrices()
