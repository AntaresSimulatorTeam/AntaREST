import configparser

import pytest
from pydantic import ValidationError

from antarest.study.storage.rawstudy.io.reader import IniReader
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    transform_name_to_id,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.command_reverter import (
    CommandReverter,
)
from antarest.study.common.default_values import (
    FilteringOptions,
    LinkProperties,
)
from antarest.study.storage.variantstudy.model.command.create_area import (
    CreateArea,
)
from antarest.study.storage.variantstudy.model.command.create_link import (
    CreateLink,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.remove_area import (
    RemoveArea,
)
from antarest.study.storage.variantstudy.model.command.remove_link import (
    RemoveLink,
)
from antarest.study.storage.variantstudy.model.command.replace_matrix import (
    ReplaceMatrix,
)
from antarest.study.storage.variantstudy.model.command.update_config import (
    UpdateConfig,
)
from antarest.study.storage.variantstudy.model.command_context import (
    CommandContext,
)


class TestCreateLink:
    def test_validation(
        self, empty_study: FileStudy, command_context: CommandContext
    ):
        area1 = "Area1"
        area1_id = transform_name_to_id(area1)

        area2 = "Area2"
        area2_id = transform_name_to_id(area2)

        CreateArea.parse_obj(
            {
                "area_name": area1,
                "command_context": command_context,
            }
        ).apply(empty_study)

        CreateArea.parse_obj(
            {
                "area_name": area2,
                "command_context": command_context,
            }
        ).apply(empty_study)

        with pytest.raises(ValidationError):
            create_link_command: ICommand = CreateLink(
                area1=area1_id,
                area2=area1_id,
                parameters={},
                command_context=command_context,
                series=[[0]],
            )

    def test_apply(
        self, empty_study: FileStudy, command_context: CommandContext
    ):
        study_path = empty_study.config.study_path
        area1 = "Area1"
        area1_id = transform_name_to_id(area1)

        area2 = "Area2"
        area2_id = transform_name_to_id(area2)

        area3 = "Area3"
        area3_id = transform_name_to_id(area3)

        CreateArea.parse_obj(
            {
                "area_name": area1,
                "command_context": command_context,
            }
        ).apply(empty_study)

        CreateArea.parse_obj(
            {
                "area_name": area2,
                "command_context": command_context,
            }
        ).apply(empty_study)

        CreateArea.parse_obj(
            {
                "area_name": area3,
                "command_context": command_context,
            }
        ).apply(empty_study)

        create_link_command: ICommand = CreateLink(
            area1=area1_id,
            area2=area2_id,
            parameters={},
            command_context=command_context,
            series=[[0]],
        )
        output = create_link_command.apply(
            study_data=empty_study,
        )

        assert output.status

        assert (
            study_path / "input" / "links" / area1_id / f"{area2_id}.txt.link"
        ).exists()

        link = IniReader()
        link_data = link.read(
            study_path / "input" / "links" / area1_id / "properties.ini"
        )
        assert (
            link_data[area2_id]["hurdles-cost"] == LinkProperties.HURDLES_COST
        )
        assert link_data[area2_id]["loop-flow"] == LinkProperties.LOOP_FLOW
        assert (
            link_data[area2_id]["use-phase-shifter"]
            == LinkProperties.USE_PHASE_SHIFTER
        )
        assert (
            str(link_data[area2_id]["transmission-capacities"])
            == LinkProperties.TRANSMISSION_CAPACITIES
        )
        assert (
            str(link_data[area2_id]["asset-type"]) == LinkProperties.ASSET_TYPE
        )
        assert (
            str(link_data[area2_id]["link-style"]) == LinkProperties.LINK_STYLE
        )
        assert (
            int(link_data[area2_id]["link-width"]) == LinkProperties.LINK_WIDTH
        )
        assert int(link_data[area2_id]["colorr"]) == LinkProperties.COLORR
        assert int(link_data[area2_id]["colorg"]) == LinkProperties.COLORG
        assert int(link_data[area2_id]["colorb"]) == LinkProperties.COLORB
        assert (
            link_data[area2_id]["display-comments"]
            == LinkProperties.DISPLAY_COMMENTS
        )
        assert (
            str(link_data[area2_id]["filter-synthesis"])
            == FilteringOptions.FILTER_SYNTHESIS
        )
        assert (
            str(link_data[area2_id]["filter-year-by-year"])
            == FilteringOptions.FILTER_YEAR_BY_YEAR
        )

        empty_study.config.version = 820
        create_link_command: ICommand = CreateLink(
            area1=area2_id,
            area2=area3_id,
            parameters={},
            command_context=command_context,
            series=[[0]],
        )
        output = create_link_command.apply(
            study_data=empty_study,
        )
        assert output.status
        empty_study.config.version = 800

        assert (
            study_path
            / "input"
            / "links"
            / area2_id
            / f"{area3_id}_parameters.txt.link"
        ).exists()
        assert (
            study_path
            / "input"
            / "links"
            / area2_id
            / "capacities"
            / f"{area3_id}_direct.txt.link"
        ).exists()
        assert (
            study_path
            / "input"
            / "links"
            / area2_id
            / "capacities"
            / f"{area3_id}_indirect.txt.link"
        ).exists()

        # TODO:assert matrix default content : 1 column, 8760 rows, value = 1

        output = CreateLink.parse_obj(
            {
                "area1": area1_id,
                "area2": area2_id,
                "parameters": {},
                "series": [[0]],
                "command_context": command_context,
            }
        ).apply(study_data=empty_study)

        assert not output.status

        parameters = {
            "hurdles-cost": "true",
            "loop-flow": "true",
            "use-phase-shifter": "true",
            "transmission-capacities": "disabled",
            "asset-type": "dc",
            "link-style": "other",
            "link-width": 12,
            "colorr": 120,
            "colorg": 120,
            "colorb": 120,
            "display-comments": "true",
            "filter-synthesis": "hourly",
            "filter-year-by-year": "hourly",
        }

        create_link_command: ICommand = CreateLink.parse_obj(
            {
                "area1": area3_id,
                "area2": area1_id,
                "parameters": parameters,
                "series": [[0]],
                "command_context": command_context,
            }
        )
        output = create_link_command.apply(
            study_data=empty_study,
        )

        assert output.status

        assert (
            study_path / "input" / "links" / area1_id / f"{area3_id}.txt.link"
        ).exists()

        link = configparser.ConfigParser()
        link.read(study_path / "input" / "links" / area1_id / "properties.ini")
        assert (
            str(link[area3_id]["hurdles-cost"]) == parameters["hurdles-cost"]
        )
        assert str(link[area3_id]["loop-flow"]) == parameters["loop-flow"]
        assert (
            str(link[area3_id]["use-phase-shifter"])
            == parameters["use-phase-shifter"]
        )
        assert (
            str(link[area3_id]["transmission-capacities"])
            == parameters["transmission-capacities"]
        )
        assert str(link[area3_id]["asset-type"]) == parameters["asset-type"]
        assert str(link[area3_id]["link-style"]) == parameters["link-style"]
        assert int(link[area3_id]["link-width"]) == parameters["link-width"]
        assert int(link[area3_id]["colorr"]) == parameters["colorr"]
        assert int(link[area3_id]["colorg"]) == parameters["colorg"]
        assert int(link[area3_id]["colorb"]) == parameters["colorb"]
        assert (
            str(link[area3_id]["display-comments"])
            == parameters["display-comments"]
        )
        assert (
            str(link[area3_id]["filter-synthesis"])
            == parameters["filter-synthesis"]
        )
        assert (
            str(link[area3_id]["filter-year-by-year"])
            == parameters["filter-year-by-year"]
        )

        output = create_link_command.apply(
            study_data=empty_study,
        )
        assert not output.status

        output = CreateLink(
            area1="does_not_exist",
            area2=area2_id,
            parameters={},
            series=[[0]],
            command_context=command_context,
        ).apply(empty_study)
        assert not output.status


def test_match(command_context: CommandContext):
    base = CreateLink(
        area1="foo", area2="bar", series=[[0]], command_context=command_context
    )
    other_match = CreateLink(
        area1="foo", area2="bar", series=[[0]], command_context=command_context
    )
    other_not_match = CreateLink(
        area1="foo", area2="baz", command_context=command_context
    )
    other_other = RemoveArea(id="id", command_context=command_context)
    assert base.match(other_match)
    assert not base.match(other_not_match)
    assert not base.match(other_other)
    assert base.match_signature() == "create_link%foo%bar"
    assert base.get_inner_matrices() == ["matrix_id"]


def test_revert(command_context: CommandContext):
    base = CreateLink(
        area1="foo", area2="bar", series=[[0]], command_context=command_context
    )
    assert CommandReverter().revert(base, [], None) == [
        RemoveLink(
            area1="foo",
            area2="bar",
            command_context=command_context,
        )
    ]


def test_create_diff(command_context: CommandContext):
    base = CreateLink(
        area1="foo", area2="bar", series="a", command_context=command_context
    )
    other_match = CreateLink(
        area1="foo",
        area2="bar",
        parameters={"hurdles-cost": "true"},
        series="b",
        command_context=command_context,
    )
    assert base.create_diff(other_match) == [
        UpdateConfig(
            target=f"input/links/bar/properties/foo",
            data=CreateLink.generate_link_properties({"hurdles-cost": "true"}),
            command_context=command_context,
        ),
        ReplaceMatrix(
            target=f"@links_series/bar/foo",
            matrix="b",
            command_context=command_context,
        ),
    ]
