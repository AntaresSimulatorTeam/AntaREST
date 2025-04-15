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
from abc import ABCMeta
from typing import Any, Dict, List, Optional, Union

from pydantic import ValidationInfo, field_validator, model_validator
from typing_extensions import override

from antarest.core.exceptions import LinkValidationError
from antarest.core.utils.utils import assert_this
from antarest.matrixstore.model import MatrixData
from antarest.study.business.model.link_model import LinkFileData
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.model import STUDY_VERSION_8_2
from antarest.study.storage.variantstudy.business.utils import strip_matrix_protocol, validate_matrix
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
    CommandOutput,
    command_failed,
    command_succeeded,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO

MATRIX_ATTRIBUTES = ["series", "direct", "indirect"]


class AbstractLinkCommand(ICommand, metaclass=ABCMeta):
    command_name: CommandName

    # Command parameters
    # ==================

    area1: str
    area2: str
    parameters: Optional[Dict[str, Any]] = None
    series: Optional[Union[List[List[MatrixData]], str]] = None
    direct: Optional[Union[List[List[MatrixData]], str]] = None
    indirect: Optional[Union[List[List[MatrixData]], str]] = None

    @field_validator("series", "direct", "indirect", mode="before")
    def validate_series(
        cls, v: Optional[Union[List[List[MatrixData]], str]], values: Union[Dict[str, Any], ValidationInfo]
    ) -> Optional[Union[List[List[MatrixData]], str]]:
        new_values = values if isinstance(values, dict) else values.data
        return validate_matrix(v, new_values) if v is not None else v

    @model_validator(mode="after")
    def validate_areas(self) -> "AbstractLinkCommand":
        if self.area1 == self.area2:
            raise ValueError("Cannot create link on same node")

        if self.study_version < STUDY_VERSION_8_2 and (self.direct is not None or self.indirect is not None):
            raise LinkValidationError(
                "The fields 'direct' and 'indirect' cannot be provided when the version is less than 820."
            )

        return self

    @override
    def to_dto(self) -> CommandDTO:
        args = {
            "area1": self.area1,
            "area2": self.area2,
            "parameters": self.parameters,
        }
        for attr in MATRIX_ATTRIBUTES:
            if value := getattr(self, attr, None):
                args[attr] = strip_matrix_protocol(value)
        return CommandDTO(action=self.command_name.value, args=args, study_version=self.study_version)

    @override
    def get_inner_matrices(self) -> List[str]:
        list_matrices = []
        for attr in MATRIX_ATTRIBUTES:
            if value := getattr(self, attr, None):
                assert_this(isinstance(value, str))
                list_matrices.append(strip_matrix_protocol(value))
        return list_matrices


class CreateLink(AbstractLinkCommand):
    """
    Command used to create a link between two areas.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.CREATE_LINK
    version: int = 1

    @override
    def _apply_dao(self, study_data: StudyDao, listener: Optional[ICommandListener] = None) -> CommandOutput:
        if study_data.link_exists(self.area1, self.area2):
            return command_failed(f"Link between '{self.area1}' and '{self.area2}' already exists")

        link = LinkFileData.model_validate(self.parameters or {}).to_dto(self.study_version, self.area1, self.area2)
        study_data.save_link(link)

        series = self.series or (
            self.command_context.generator_matrix_constants.get_link(version=study_data.get_version())
        )
        direct = self.direct or (self.command_context.generator_matrix_constants.get_link_direct())
        indirect = self.indirect or (self.command_context.generator_matrix_constants.get_link_indirect())

        area_from, area_to = sorted((self.area1, self.area2))
        study_data.save_link_series(area_from, area_to, str(series))
        study_data.save_link_direct_capacities(area_from, area_to, str(direct))
        study_data.save_link_indirect_capacities(area_from, area_to, str(indirect))

        return command_succeeded(f"Link between '{self.area1}' and '{self.area2}' created")
