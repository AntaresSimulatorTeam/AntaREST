from typing import Dict, List, Union, Any, Optional, cast, Tuple

from pydantic import validator

from antarest.core.model import JSON
from antarest.core.utils.utils import assert_this
from antarest.matrixstore.model import MatrixData
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    Link,
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.common.default_values import (
    LinkProperties,
    FilteringOptions,
)
from antarest.study.storage.variantstudy.business.utils import (
    validate_matrix,
    strip_matrix_protocol,
)
from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.icommand import (
    ICommand,
    MATCH_SIGNATURE_SEPARATOR,
)
from antarest.study.storage.variantstudy.model.model import CommandDTO


class LinkAlreadyExistError(Exception):
    pass


class CreateLink(ICommand):
    area1: str
    area2: str
    parameters: Optional[Dict[str, str]] = None
    series: Optional[Union[List[List[MatrixData]], str]] = None
    direct: Optional[Union[List[List[MatrixData]], str]] = None
    indirect: Optional[Union[List[List[MatrixData]], str]] = None

    def __init__(self, **data: Any) -> None:
        super().__init__(
            command_name=CommandName.CREATE_LINK, version=1, **data
        )

    @validator("series", "direct", "indirect", always=True)
    def validate_series(
        cls, v: Optional[Union[List[List[MatrixData]], str]], values: Any
    ) -> Optional[Union[List[List[MatrixData]], str]]:
        if v is not None:
            return validate_matrix(v, values)
        return v

    def _create_link_in_config(
        self, area_from: str, area_to: str, study_data: FileStudyTreeConfig
    ) -> None:
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

    @staticmethod
    def generate_link_properties(parameters: JSON) -> JSON:
        return {
            "hurdles-cost": parameters.get(
                "hurdles-cost",
                LinkProperties.HURDLES_COST,
            ),
            "loop-flow": parameters.get("loop-flow", LinkProperties.LOOP_FLOW),
            "use-phase-shifter": parameters.get(
                "use-phase-shifter",
                LinkProperties.USE_PHASE_SHIFTER,
            ),
            "transmission-capacities": parameters.get(
                "transmission-capacities",
                LinkProperties.TRANSMISSION_CAPACITIES,
            ),
            "asset-type": parameters.get(
                "asset-type",
                LinkProperties.ASSET_TYPE,
            ),
            "link-style": parameters.get(
                "link-style",
                LinkProperties.LINK_STYLE,
            ),
            "link-width": parameters.get(
                "link-width",
                LinkProperties.LINK_WIDTH,
            ),
            "colorr": parameters.get("colorr", LinkProperties.COLORR),
            "colorg": parameters.get("colorg", LinkProperties.COLORG),
            "colorb": parameters.get("colorb", LinkProperties.COLORB),
            "display-comments": parameters.get(
                "display-comments",
                LinkProperties.DISPLAY_COMMENTS,
            ),
            "filter-synthesis": parameters.get(
                "filter-synthesis",
                FilteringOptions.FILTER_SYNTHESIS,
            ),
            "filter-year-by-year": parameters.get(
                "filter-year-by-year",
                FilteringOptions.FILTER_YEAR_BY_YEAR,
            ),
        }

    def _apply_config(
        self, study_data: FileStudyTreeConfig
    ) -> Tuple[CommandOutput, Dict[str, Any]]:
        if self.area1 not in study_data.areas:
            return (
                CommandOutput(
                    status=False,
                    message=f"The area '{self.area1}' does not exist",
                ),
                dict(),
            )
        if self.area2 not in study_data.areas:
            return (
                CommandOutput(
                    status=False,
                    message=f"The area '{self.area2}' does not exist",
                ),
                dict(),
            )

        area_from, area_to = sorted([self.area1, self.area2])
        if area_to in study_data.areas[area_from].links:
            return (
                CommandOutput(
                    status=False,
                    message=f"The link between {self.area1} and {self.area2} already exist.",
                ),
                dict(),
            )

        self._create_link_in_config(area_from, area_to, study_data)

        if (
            study_data.path / "input" / "links" / area_from / f"{area_to}.txt"
        ).exists():
            return (
                CommandOutput(
                    status=False,
                    message=f"The link between {self.area1} and {self.area2} already exist",
                ),
                dict(),
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

        self.parameters = self.parameters or {}
        link_property = CreateLink.generate_link_properties(self.parameters)

        study_data.tree.save(
            link_property, ["input", "links", area_from, "properties", area_to]
        )
        self.series = self.series or (
            self.command_context.generator_matrix_constants.get_link(
                version=version
            )
        )
        self.direct = self.direct or (
            self.command_context.generator_matrix_constants.get_link_direct()
        )
        self.indirect = self.indirect or (
            self.command_context.generator_matrix_constants.get_link_indirect()
        )

        assert type(self.series) is str
        if version < 820:
            study_data.tree.save(
                self.series, ["input", "links", area_from, area_to]
            )
        else:
            study_data.tree.save(
                self.series,
                ["input", "links", area_from, f"{area_to}_parameters"],
            )

            study_data.tree.save(
                {}, ["input", "links", area_from, "capacities"]
            )
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
            self.command_name.value
            + MATCH_SIGNATURE_SEPARATOR
            + self.area1
            + MATCH_SIGNATURE_SEPARATOR
            + self.area2
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
        from antarest.study.storage.variantstudy.model.command.update_config import (
            UpdateConfig,
        )
        from antarest.study.storage.variantstudy.model.command.replace_matrix import (
            ReplaceMatrix,
        )

        commands: List[ICommand] = []
        area_from, area_to = sorted([self.area1, self.area2])
        if self.parameters != other.parameters:
            link_property = CreateLink.generate_link_properties(
                other.parameters or {}
            )
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
