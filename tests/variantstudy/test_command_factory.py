import importlib
import pkgutil
from unittest.mock import Mock

import pytest
from antarest.matrixstore.service import MatrixService
from antarest.study.storage.patch_service import PatchService
from antarest.study.storage.variantstudy.business.matrix_constants_generator import (
    GeneratorMatrixConstants,
)
from antarest.study.storage.variantstudy.business.utils import remove_none_args
from antarest.study.storage.variantstudy.command_factory import CommandFactory
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.model import CommandDTO


class TestCommandFactory:
    # noinspection SpellCheckingInspection
    def setup_class(self):
        """
        Set up the test class.

        Imports all modules from the `antarest.study.storage.variantstudy.model.command` package
        and creates a set of command class names derived from the `ICommand` abstract class.
        The objective is to ensure that the unit test covers all commands in this package.

        This method is executed once before any tests in the test class are run.
        """
        for module_loader, name, ispkg in pkgutil.iter_modules(
            ["antarest/study/storage/variantstudy/model/command"]
        ):
            importlib.import_module(
                f".{name}",
                package="antarest.study.storage.variantstudy.model.command",
            )
        self.command_class_set = {
            command.__name__ for command in ICommand.__subclasses__()
        }

    # noinspection SpellCheckingInspection
    @pytest.mark.parametrize(
        "command_dto",
        [
            CommandDTO(
                action=CommandName.CREATE_AREA.value,
                args={"area_name": "area_name"},
            ),
            CommandDTO(
                action=CommandName.CREATE_AREA.value,
                args=[
                    {"area_name": "area_name"},
                    {"area_name": "area2"},
                ],
            ),
            CommandDTO(
                action=CommandName.REMOVE_AREA.value,
                args={"id": "id"},
            ),
            CommandDTO(
                action=CommandName.REMOVE_AREA.value,
                args=[{"id": "id"}],
            ),
            CommandDTO(
                action=CommandName.CREATE_DISTRICT.value,
                args={
                    "name": "id",
                    "filter_items": ["a"],
                    "output": True,
                    "comments": "",
                },
            ),
            CommandDTO(
                action=CommandName.CREATE_DISTRICT.value,
                args=[
                    {
                        "name": "id",
                        "base_filter": "add-all",
                        "output": True,
                        "comments": "",
                    }
                ],
            ),
            CommandDTO(
                action=CommandName.REMOVE_DISTRICT.value,
                args={"id": "id"},
            ),
            CommandDTO(
                action=CommandName.REMOVE_DISTRICT.value,
                args=[{"id": "id"}],
            ),
            CommandDTO(
                action=CommandName.CREATE_LINK.value,
                args={
                    "area1": "area1",
                    "area2": "area2",
                    "parameters": {},
                    "series": "series",
                },
            ),
            CommandDTO(
                action=CommandName.CREATE_LINK.value,
                args=[
                    {
                        "area1": "area1",
                        "area2": "area2",
                        "parameters": {},
                        "series": "series",
                    }
                ],
            ),
            CommandDTO(
                action=CommandName.REMOVE_LINK.value,
                args={
                    "area1": "area1",
                    "area2": "area2",
                },
            ),
            CommandDTO(
                action=CommandName.REMOVE_LINK.value,
                args=[
                    {
                        "area1": "area1",
                        "area2": "area2",
                    }
                ],
            ),
            CommandDTO(
                action=CommandName.CREATE_BINDING_CONSTRAINT.value,
                args={
                    "name": "name",
                    "enabled": True,
                    "time_step": "hourly",
                    "operator": "equal",
                    "coeffs": {},
                    "values": "values",
                },
            ),
            CommandDTO(
                action=CommandName.CREATE_BINDING_CONSTRAINT.value,
                args=[
                    {
                        "name": "name",
                        "enabled": True,
                        "time_step": "hourly",
                        "operator": "equal",
                        "coeffs": {},
                        "values": "values",
                    }
                ],
            ),
            CommandDTO(
                action=CommandName.UPDATE_BINDING_CONSTRAINT.value,
                args={
                    "id": "id",
                    "enabled": True,
                    "time_step": "hourly",
                    "operator": "equal",
                    "coeffs": {},
                    "values": "values",
                },
            ),
            CommandDTO(
                action=CommandName.UPDATE_BINDING_CONSTRAINT.value,
                args=[
                    {
                        "id": "id",
                        "enabled": True,
                        "time_step": "hourly",
                        "operator": "equal",
                        "coeffs": {},
                    }
                ],
            ),
            CommandDTO(
                action=CommandName.REMOVE_BINDING_CONSTRAINT.value,
                args={"id": "id"},
            ),
            CommandDTO(
                action=CommandName.REMOVE_BINDING_CONSTRAINT.value,
                args=[{"id": "id"}],
            ),
            CommandDTO(
                action=CommandName.CREATE_THERMAL_CLUSTER.value,
                args={
                    "area_id": "area_name",
                    "cluster_name": "cluster_name",
                    "parameters": {
                        "group": "group",
                        "unitcount": "unitcount",
                        "nominalcapacity": "nominalcapacity",
                        "marginal-cost": "marginal-cost",
                        "market-bid-cost": "market-bid-cost",
                    },
                    "prepro": "prepro",
                    "modulation": "modulation",
                },
            ),
            CommandDTO(
                action=CommandName.CREATE_THERMAL_CLUSTER.value,
                args=[
                    {
                        "area_id": "area_name",
                        "cluster_name": "cluster_name",
                        "parameters": {
                            "group": "group",
                            "unitcount": "unitcount",
                            "nominalcapacity": "nominalcapacity",
                            "marginal-cost": "marginal-cost",
                            "market-bid-cost": "market-bid-cost",
                        },
                        "prepro": "prepro",
                        "modulation": "modulation",
                    }
                ],
            ),
            CommandDTO(
                action=CommandName.REMOVE_THERMAL_CLUSTER.value,
                args={"area_id": "area_name", "cluster_id": "cluster_name"},
            ),
            CommandDTO(
                action=CommandName.REMOVE_THERMAL_CLUSTER.value,
                args=[{"area_id": "area_name", "cluster_id": "cluster_name"}],
            ),
            CommandDTO(
                action=CommandName.CREATE_RENEWABLES_CLUSTER.value,
                args={
                    "area_id": "area_name",
                    "cluster_name": "cluster_name",
                    "parameters": {
                        "name": "name",
                        "ts-interpretation": "power-generation",
                    },
                },
            ),
            CommandDTO(
                action=CommandName.CREATE_RENEWABLES_CLUSTER.value,
                args=[
                    {
                        "area_id": "area_name",
                        "cluster_name": "cluster_name",
                        "parameters": {
                            "name": "name",
                            "ts-interpretation": "power-generation",
                        },
                    }
                ],
            ),
            CommandDTO(
                action=CommandName.REMOVE_RENEWABLES_CLUSTER.value,
                args={"area_id": "area_name", "cluster_id": "cluster_name"},
            ),
            CommandDTO(
                action=CommandName.REMOVE_RENEWABLES_CLUSTER.value,
                args=[{"area_id": "area_name", "cluster_id": "cluster_name"}],
            ),
            CommandDTO(
                action=CommandName.REPLACE_MATRIX.value,
                args={"target": "target_element", "matrix": "matrix"},
            ),
            CommandDTO(
                action=CommandName.REPLACE_MATRIX.value,
                args=[{"target": "target_element", "matrix": "matrix"}],
            ),
            CommandDTO(
                action=CommandName.UPDATE_CONFIG.value,
                args={"target": "target", "data": {}},
            ),
            CommandDTO(
                action=CommandName.UPDATE_CONFIG.value,
                args=[{"target": "target", "data": {}}],
            ),
            CommandDTO(
                action=CommandName.UPDATE_COMMENTS.value,
                args={"comments": "comments"},
            ),
            CommandDTO(
                action=CommandName.UPDATE_COMMENTS.value,
                args=[{"comments": "comments"}],
            ),
            CommandDTO(
                action=CommandName.UPDATE_FILE.value,
                args={
                    "target": "settings/resources/study",
                    "b64Data": "",
                },
            ),
            CommandDTO(
                action=CommandName.UPDATE_DISTRICT.value,
                args={"id": "id", "filter_items": ["a"]},
            ),
            CommandDTO(
                action=CommandName.UPDATE_DISTRICT.value,
                args=[{"id": "id", "base_filter": "add-all"}],
            ),
            CommandDTO(
                action=CommandName.UPDATE_PLAYLIST.value,
                args=[{"active": True, "items": [1, 3], "reverse": False}],
            ),
            CommandDTO(
                action=CommandName.UPDATE_PLAYLIST.value,
                args={
                    "active": True,
                    "items": [1, 3],
                    "weights": {1: 5.0},
                    "reverse": False,
                },
            ),
            CommandDTO(
                action=CommandName.UPDATE_SCENARIO_BUILDER.value,
                args={
                    "data": {
                        "ruleset test": {
                            "l": {"area1": {"0": 1}},
                            "ntc": {"area1 / area2": {"1": 23}},
                            "t": {"area1": {"thermal": {"1": 2}}},
                        },
                    }
                },
            ),
            CommandDTO(
                action=CommandName.CREATE_ST_STORAGE.value,
                args={
                    "area_id": "area 1",
                    "storage_name": "Storage 1",
                    "parameters": {"name": "Storage 1", "group": "Battery"},
                    "pmax_injection": "matrix://59ea6c83-6348-466d-9530-c35c51ca4c37",
                    "pmax_withdrawal": "matrix://5f988548-dadc-4bbb-8ce8-87a544dbf756",
                    "lower_rule_curve": "matrix://8ce4fcea-cc97-4d2c-b641-a27a53454612",
                    "upper_rule_curve": "matrix://8ce614c8-c687-41af-8b24-df8a49cc52af",
                    "inflows": "matrix://df9b25e1-e3f7-4a57-8182-0ff9791439e5",
                },
            ),
            CommandDTO(
                action=CommandName.CREATE_ST_STORAGE.value,
                args=[
                    {
                        "area_id": "area 1",
                        "storage_name": "Storage 1",
                        "parameters": {
                            "name": "Storage 1",
                            "group": "Battery",
                        },
                        "pmax_injection": "matrix://59ea6c83-6348-466d-9530-c35c51ca4c37",
                        "pmax_withdrawal": "matrix://5f988548-dadc-4bbb-8ce8-87a544dbf756",
                        "lower_rule_curve": "matrix://8ce4fcea-cc97-4d2c-b641-a27a53454612",
                        "upper_rule_curve": "matrix://8ce614c8-c687-41af-8b24-df8a49cc52af",
                        "inflows": "matrix://df9b25e1-e3f7-4a57-8182-0ff9791439e5",
                    },
                    {
                        "area_id": "area 1",
                        "storage_name": "Storage 2",
                        "parameters": {
                            "name": "Storage 2",
                            "group": "Battery",
                            "efficiency": 0.94,
                        },
                        "pmax_injection": "matrix://3f5b3746-3995-49b7-a6da-622633472e05",
                        "pmax_withdrawal": "matrix://4b64a31f-927b-4887-b4cd-adcddd39bdcd",
                        "lower_rule_curve": "matrix://16c7c3ae-9824-4ef2-aa68-51145884b025",
                        "upper_rule_curve": "matrix://9a6104e9-990a-415f-a6e2-57507e13b58c",
                        "inflows": "matrix://e8923768-9bdd-40c2-a6ea-2da2523be727",
                    },
                ],
            ),
            CommandDTO(
                action=CommandName.REMOVE_ST_STORAGE.value,
                args={
                    "area_id": "area 1",
                    "storage_id": "storage 1",
                },
            ),
            CommandDTO(
                action=CommandName.REMOVE_ST_STORAGE.value,
                args=[
                    {
                        "area_id": "area 1",
                        "storage_id": "storage 1",
                    },
                    {
                        "area_id": "area 1",
                        "storage_id": "storage 2",
                    },
                ],
            ),
        ],
    )
    @pytest.mark.unit_test
    def test_command_factory(self, command_dto: CommandDTO):
        command_factory = CommandFactory(
            generator_matrix_constants=Mock(spec=GeneratorMatrixConstants),
            matrix_service=Mock(spec=MatrixService),
            patch_service=Mock(spec=PatchService),
        )
        command_list = command_factory.to_command(command_dto=command_dto)
        if isinstance(args := command_dto.args, dict):
            assert len(command_list) == 1
            assert remove_none_args(command_list[0].to_dto()) == command_dto
        else:
            assert len(command_list) == len(args)

        for command in command_list:
            assert command.command_name.value == command_dto.action

        self.command_class_set.discard(type(command_list[0]).__name__)

    def teardown_class(self):
        # Check that all command classes have been tested
        assert not self.command_class_set


@pytest.mark.unit_test
def test_unknown_command():
    with pytest.raises(NotImplementedError):
        command_factory = CommandFactory(
            generator_matrix_constants=Mock(spec=GeneratorMatrixConstants),
            matrix_service=Mock(spec=MatrixService),
            patch_service=Mock(spec=PatchService),
        )
        command_factory.to_command(
            command_dto=CommandDTO(action="unknown_command", args={})
        )
