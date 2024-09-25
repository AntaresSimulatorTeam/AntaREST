# Copyright (c) 2024, RTE (https://www.rte-france.com)
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
from typing import Any, Dict, List, Optional, Tuple, Union, cast

from pydantic import AliasGenerator, BaseModel, Field, ValidationInfo, field_validator, model_validator

from antarest.core.utils.string import to_kebab_case
from antarest.core.utils.utils import assert_this
from antarest.matrixstore.model import MatrixData
from antarest.study.storage.rawstudy.model.filesystem.config.links import AssetType, LinkStyle, TransmissionCapacity
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig, Link
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.utils import strip_matrix_protocol, validate_matrix
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput, FilteringOptions
from antarest.study.storage.variantstudy.model.command.icommand import MATCH_SIGNATURE_SEPARATOR, ICommand
from antarest.study.storage.variantstudy.model.model import CommandDTO

DEFAULT_COLOR = 112


class AreaInfo(BaseModel):
    area1: str
    area2: str


class LinkInfoProperties(BaseModel):
    hurdles_cost: Optional[bool] = Field(False, alias="hurdles-cost")
    loop_flow: Optional[bool] = Field(False, alias="loop-flow")
    use_phase_shifter: Optional[bool] = Field(False, alias="use-phase-shifter")
    transmission_capacities: Optional[TransmissionCapacity] = Field(
        TransmissionCapacity.ENABLED, alias="transmission-capacities"
    )
    asset_type: Optional[AssetType] = Field(AssetType.AC, alias="asset-type")
    display_comments: Optional[bool] = Field(True, alias="display-comments")
    colorr: Optional[int] = DEFAULT_COLOR
    colorb: Optional[int] = DEFAULT_COLOR
    colorg: Optional[int] = DEFAULT_COLOR
    link_width: Optional[float] = Field(1, alias="link-width")
    link_style: Optional[LinkStyle] = Field(LinkStyle.PLAIN, alias="link-style")

    @model_validator(mode="before")
    def validate_colors(cls, values: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
        if type(values) is dict:
            colors = {
                "colorr": values.get("colorr"),
                "colorb": values.get("colorb"),
                "colorg": values.get("colorg"),
            }
            for color_name, color_value in colors.items():
                if color_value is not None and (color_value < 0 or color_value > 255):
                    raise ValueError(f"Invalid value for {color_name}. Must be between 0 and 255.")

        return values


class LinkInfoProperties820(LinkInfoProperties):
    filter_synthesis: Optional[str] = Field(None, alias="filter-synthesis")
    filter_year_by_year: Optional[str] = Field(None, alias="filter-year-by-year")

    @field_validator('filter_synthesis', 'filter_year_by_year', mode="before")
    def validate_individual_filters(cls, value: Optional[str], field) -> Optional[str]:
        if value is not None:
            filter_options = ["hourly", "daily", "weekly", "monthly", "annual"]
            options = value.replace(" ", "").split(",")
            invalid_options = [opt for opt in options if opt not in filter_options]
            if invalid_options:
                raise ValueError(
                    f"Invalid value(s) in '{field.alias}': {', '.join(invalid_options)}. "
                    f"Allowed values are: {', '.join(filter_options)}."
                )
        return value


class LinkProperties(LinkInfoProperties820, alias_generator=AliasGenerator(serialization_alias=to_kebab_case)):
    pass


class CreateLink(ICommand):
    """
    Command used to create a link between two areas.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.CREATE_LINK
    version: int = 1

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

    def _apply_config(self, study_data: FileStudyTreeConfig) -> Tuple[CommandOutput, Dict[str, Any]]:
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

        if self.area1 == self.area2:
            return (
                CommandOutput(
                    status=False,
                    message="Cannot create link between the same node",
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

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        version = study_data.config.version
        output, data = self._apply_config(study_data.config)
        if not output.status:
            return output
        area_from = data["area_from"]
        area_to = data["area_to"]

        properties = LinkProperties.model_validate(self.parameters or {})
        excludes = set() if version >= 820 else {"filter_synthesis", "filter_year_by_year"}
        link_property = properties.model_dump(mode="json", exclude=excludes, by_alias=True, exclude_none=True)

        study_data.tree.save(link_property, ["input", "links", area_from, "properties", area_to])
        self.series = self.series or (self.command_context.generator_matrix_constants.get_link(version=version))
        self.direct = self.direct or (self.command_context.generator_matrix_constants.get_link_direct())
        self.indirect = self.indirect or (self.command_context.generator_matrix_constants.get_link_indirect())

        assert type(self.series) is str
        if version < 820:
            study_data.tree.save(self.series, ["input", "links", area_from, area_to])
        else:
            study_data.tree.save(
                self.series,
                ["input", "links", area_from, f"{area_to}_parameters"],
            )

            study_data.tree.save({}, ["input", "links", area_from, "capacities"])
            if self.direct:
                assert isinstance(self.direct, str)
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

            if self.indirect:
                assert isinstance(self.indirect, str)
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

        return output

    def to_dto(self) -> CommandDTO:
        args = {
            "area1": self.area1,
            "area2": self.area2,
            "parameters": self.parameters,
        }
        if self.series:
            args["series"] = strip_matrix_protocol(self.series)
        if self.direct:
            args["direct"] = strip_matrix_protocol(self.direct)
        if self.indirect:
            args["indirect"] = strip_matrix_protocol(self.indirect)
        return CommandDTO(
            action=CommandName.CREATE_LINK.value,
            args=args,
        )

    def match_signature(self) -> str:
        return str(
            self.command_name.value + MATCH_SIGNATURE_SEPARATOR + self.area1 + MATCH_SIGNATURE_SEPARATOR + self.area2
        )

    def match(self, other: ICommand, equal: bool = False) -> bool:
        if not isinstance(other, CreateLink):
            return False
        simple_match = self.area1 == other.area1 and self.area2 == other.area2
        if not equal:
            return simple_match
        return (
            simple_match
            and self.parameters == other.parameters
            and self.series == other.series
            and self.direct == other.direct
            and self.indirect == other.indirect
        )

    def _create_diff(self, other: "ICommand") -> List["ICommand"]:
        other = cast(CreateLink, other)
        from antarest.study.storage.variantstudy.model.command.replace_matrix import ReplaceMatrix
        from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig

        commands: List[ICommand] = []
        area_from, area_to = sorted([self.area1, self.area2])
        if self.parameters != other.parameters:
            properties = LinkProperties.model_validate(other.parameters or {})
            link_property = properties.model_dump(mode="json", by_alias=True, exclude_none=True)
            commands.append(
                UpdateConfig(
                    target=f"input/links/{area_from}/properties/{area_to}",
                    data=link_property,
                    command_context=self.command_context,
                )
            )
        if self.series != other.series:
            commands.append(
                ReplaceMatrix(
                    target=f"@links_series/{area_from}/{area_to}",
                    matrix=strip_matrix_protocol(other.series),
                    command_context=self.command_context,
                )
            )
        return commands

    def get_inner_matrices(self) -> List[str]:
        list_matrices = []
        if self.series:
            assert_this(isinstance(self.series, str))
            list_matrices.append(strip_matrix_protocol(self.series))
        if self.direct:
            assert_this(isinstance(self.direct, str))
            list_matrices.append(strip_matrix_protocol(self.direct))
        if self.indirect:
            assert_this(isinstance(self.indirect, str))
            list_matrices.append(strip_matrix_protocol(self.indirect))
        return list_matrices
