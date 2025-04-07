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
from typing import Any, Dict, List, Optional, Tuple, Union

from antares.study.version import StudyVersion
from pydantic import ValidationInfo, field_validator, model_validator
from typing_extensions import override

from antarest.core.exceptions import LinkValidationError
from antarest.core.utils.utils import assert_this
from antarest.matrixstore.model import MatrixData
from antarest.study.business.model.link_model import LinkInternal
from antarest.study.model import STUDY_VERSION_8_2
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig, Link
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.utils import strip_matrix_protocol, validate_matrix
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput, FilteringOptions
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

    def save_series(self, area_from: str, area_to: str, study_data: FileStudy, version: StudyVersion) -> None:
        assert isinstance(self.series, str)
        if version < STUDY_VERSION_8_2:
            study_data.tree.save(self.series, ["input", "links", area_from, area_to])
        else:
            study_data.tree.save(
                self.series,
                ["input", "links", area_from, f"{area_to}_parameters"],
            )

    def save_direct(self, area_from: str, area_to: str, study_data: FileStudy, version: StudyVersion) -> None:
        assert isinstance(self.direct, str)
        if version >= STUDY_VERSION_8_2:
            study_data.tree.save(
                self.direct,
                [
                    "input",
                    "links",
                    area_from,
                    "capacities",
                    f"{area_to}_direct",
                ],
            )

    def save_indirect(self, area_from: str, area_to: str, study_data: FileStudy, version: StudyVersion) -> None:
        assert isinstance(self.indirect, str)
        if version >= STUDY_VERSION_8_2:
            study_data.tree.save(
                self.indirect,
                [
                    "input",
                    "links",
                    area_from,
                    "capacities",
                    f"{area_to}_indirect",
                ],
            )


class CreateLink(AbstractLinkCommand):
    """
    Command used to create a link between two areas.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.CREATE_LINK
    version: int = 1

    def _create_link_in_config(self, area_from: str, area_to: str, study_data: FileStudyTreeConfig) -> None:
        self.parameters = self.parameters or {}
        study_data.areas[area_from].links[area_to] = Link(
            filters_synthesis=[
                step.strip()
                for step in self.parameters.get(
                    "filter-synthesis",
                    FilteringOptions.FILTER_SYNTHESIS,
                ).split(",")
            ],
            filters_year=[
                step.strip()
                for step in self.parameters.get(
                    "filter-year-by-year",
                    FilteringOptions.FILTER_YEAR_BY_YEAR,
                ).split(",")
            ],
        )

    @override
    def _apply_config(self, study_data: FileStudyTreeConfig) -> Tuple[CommandOutput, Dict[str, Any]]:  # type: ignore
        pass  # TODO DELETE

    def validate_data(self, study_data: FileStudyTreeConfig) -> Tuple[CommandOutput, Dict[str, Any]]:
        if self.area1 not in study_data.areas:
            return (
                CommandOutput(
                    status=False,
                    message=f"The area '{self.area1}' does not exist",
                ),
                {},
            )
        if self.area2 not in study_data.areas:
            return (
                CommandOutput(
                    status=False,
                    message=f"The area '{self.area2}' does not exist",
                ),
                {},
            )

        # Link parameters between two areas are stored in only one of the two
        # areas in the "input/links" tree. One area acts as source (`area_from`)
        # and the other as target (`area_to`).
        # Parameters are stored in the target area (`area_to`).
        # The choice as to which area plays the role of source or target is made
        # arbitrarily by sorting the area IDs in lexicographic order.
        # The first will be the source and the second will be the target.
        area_from, area_to = sorted([self.area1, self.area2])
        if area_to in study_data.areas[area_from].links:
            return (
                CommandOutput(
                    status=False,
                    message=f"The link between {self.area1} and {self.area2} already exist.",
                ),
                {},
            )

        self._create_link_in_config(area_from, area_to, study_data)

        if (study_data.path / "input" / "links" / area_from / f"{area_to}.txt").exists():
            return (
                CommandOutput(
                    status=False,
                    message=f"The link between {self.area1} and {self.area2} already exist",
                ),
                {},
            )

        return (
            CommandOutput(
                status=True,
                message=f"Link between '{self.area1}' and '{self.area2}' created",
            ),
            {"area_from": area_from, "area_to": area_to},
        )

    @override
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        version = study_data.config.version
        output, data = self.validate_data(study_data.config)
        if not output.status:
            return output

        to_exclude = {"area1", "area2"}
        if version < STUDY_VERSION_8_2:
            to_exclude.update("filter-synthesis", "filter-year-by-year")

        validated_properties = LinkInternal.model_validate(self.parameters).model_dump(
            by_alias=True, exclude=to_exclude
        )

        area_from = data["area_from"]
        area_to = data["area_to"]

        study_data.tree.save(validated_properties, ["input", "links", area_from, "properties", area_to])

        self.series = self.series or (self.command_context.generator_matrix_constants.get_link(version=version))
        self.direct = self.direct or (self.command_context.generator_matrix_constants.get_link_direct())
        self.indirect = self.indirect or (self.command_context.generator_matrix_constants.get_link_indirect())

        self.save_series(area_from, area_to, study_data, version)
        self.save_direct(area_from, area_to, study_data, version)
        self.save_indirect(area_from, area_to, study_data, version)

        return output

    @override
    def to_dto(self) -> CommandDTO:
        return super().to_dto()

    @override
    def get_inner_matrices(self) -> List[str]:
        return super().get_inner_matrices()
