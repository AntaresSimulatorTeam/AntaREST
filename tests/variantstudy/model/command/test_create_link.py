import configparser

from antarest.matrixstore.service import MatrixService
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.default_values import (
    FilteringOptions,
    LinkProperties,
)
from antarest.study.storage.variantstudy.business.matrix_constants_generator import (
    GeneratorMatrixConstants,
)
from antarest.study.storage.variantstudy.model.command.create_area import (
    CreateArea,
)
from antarest.study.storage.variantstudy.model.command.create_link import (
    CreateLink,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_context import (
    CommandContext,
)


class TestCreateArea:
    def test_validation(self, empty_study: FileStudy):
        pass

    def test_apply(
        self, empty_study: FileStudy, matrix_service: MatrixService
    ):

        command_context = CommandContext(
            generator_matrix_constants=GeneratorMatrixConstants(
                matrix_service=matrix_service
            )
        )
        study_path = empty_study.config.study_path
        area1 = "Area1"
        area2 = "Area2"
        area3 = "Area3"

        CreateArea.parse_obj(
            {
                "area_name": area1,
                "metadata": {},
                "command_context": command_context,
            }
        ).apply(empty_study)

        CreateArea.parse_obj(
            {
                "area_name": area2,
                "metadata": {},
                "command_context": command_context,
            }
        ).apply(empty_study)

        CreateArea.parse_obj(
            {
                "area_name": area3,
                "metadata": {},
                "command_context": command_context,
            }
        ).apply(empty_study)

        command_context = CommandContext(matrix_service=matrix_service)

        create_link_command: ICommand = CreateLink(
            area1=area1,
            area2=area2,
            parameters={},
            command_context=command_context,
            series=[[0]],
        )
        output = create_link_command.apply(
            study_data=empty_study,
        )

        assert output.status

        assert (
            study_path / "input" / "links" / area1 / f"{area2}.txt.link"
        ).exists()

        link = configparser.ConfigParser()
        link.read(study_path / "input" / "links" / area1 / "properties.ini")
        test = link.sections()
        assert (
            str(link[area2]["hurldes-cost"])
            == LinkProperties.HURDLES_COST.value
        )
        assert str(link[area2]["loop-flow"]) == LinkProperties.LOOP_FLOW.value
        assert (
            str(link[area2]["use-phase-shifter"])
            == LinkProperties.USE_PHASE_SHIFTER.value
        )
        assert (
            str(link[area2]["transmission-capacities"])
            == LinkProperties.TRANSMISSION_CAPACITIES.value
        )
        assert (
            str(link[area2]["asset-type"]) == LinkProperties.ASSET_TYPE.value
        )
        assert (
            str(link[area2]["link-style"]) == LinkProperties.LINK_STYLE.value
        )
        assert (
            int(link[area2]["link-width"]) == LinkProperties.LINK_WIDTH.value
        )
        assert int(link[area2]["colorr"]) == LinkProperties.COLORR.value
        assert int(link[area2]["colorg"]) == LinkProperties.COLORG.value
        assert int(link[area2]["colorb"]) == LinkProperties.COLORB.value
        assert (
            str(link[area2]["display-comments"])
            == LinkProperties.DISPLAY_COMMENTS.value
        )
        assert (
            str(link[area2]["filter-synthesis"])
            == FilteringOptions.FILTER_SYNTHESIS.value
        )
        assert (
            str(link[area2]["filter-year-by-year"])
            == FilteringOptions.FILTER_YEAR_BY_YEAR.value
        )

        output = CreateLink.parse_obj(
            {
                "area1": area1,
                "area2": area2,
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
                "area1": area3,
                "area2": area1,
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
            study_path / "input" / "links" / area1 / f"{area3}.txt.link"
        ).exists()

        link = configparser.ConfigParser()
        link.read(study_path / "input" / "links" / area1 / "properties.ini")
        assert str(link[area3]["hurldes-cost"]) == parameters["hurdles-cost"]
        assert str(link[area3]["loop-flow"]) == parameters["loop-flow"]
        assert (
            str(link[area3]["use-phase-shifter"])
            == parameters["use-phase-shifter"]
        )
        assert (
            str(link[area3]["transmission-capacities"])
            == parameters["transmission-capacities"]
        )
        assert str(link[area3]["asset-type"]) == parameters["asset-type"]
        assert str(link[area3]["link-style"]) == parameters["link-style"]
        assert int(link[area3]["link-width"]) == parameters["link-width"]
        assert int(link[area3]["colorr"]) == parameters["colorr"]
        assert int(link[area3]["colorg"]) == parameters["colorg"]
        assert int(link[area3]["colorb"]) == parameters["colorb"]
        assert (
            str(link[area3]["display-comments"])
            == parameters["display-comments"]
        )
        assert (
            str(link[area3]["filter-synthesis"])
            == parameters["filter-synthesis"]
        )
        assert (
            str(link[area3]["filter-year-by-year"])
            == parameters["filter-year-by-year"]
        )
