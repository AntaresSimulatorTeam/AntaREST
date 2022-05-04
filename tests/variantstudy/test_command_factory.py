import importlib
import pkgutil
from unittest.mock import Mock

import pytest

from antarest.matrixstore.service import MatrixService
from antarest.study.storage.patch_service import PatchService
from antarest.study.storage.variantstudy.business.matrix_constants_generator import (
    GeneratorMatrixConstants,
)
from antarest.study.storage.variantstudy.command_factory import CommandFactory
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.utils import (
    remove_none_args,
)
from antarest.study.storage.variantstudy.model.model import CommandDTO


class TestCommandFactory:
    def setup_class(self):
        for (module_loader, name, ispkg) in pkgutil.iter_modules(
            ["antarest/study/storage/variantstudy/model/command"]
        ):
            importlib.import_module(
                "." + name,
                package="antarest.study.storage.variantstudy.model.command",
            )
        self.command_class_set = set(
            [command.__name__ for command in ICommand.__subclasses__()]
        )

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
                args={"name": "id", "filter_items": ["a"]},
            ),
            CommandDTO(
                action=CommandName.CREATE_DISTRICT.value,
                args=[{"name": "id", "base_filter": "add-all"}],
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
                action=CommandName.CREATE_CLUSTER.value,
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
                action=CommandName.CREATE_CLUSTER.value,
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
                action=CommandName.REMOVE_CLUSTER.value,
                args={"area_id": "area_name", "cluster_id": "cluster_name"},
            ),
            CommandDTO(
                action=CommandName.REMOVE_CLUSTER.value,
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
        ],
    )
    @pytest.mark.unit_test
    def test_command_factory(self, command_dto: CommandDTO):
        command_factory = CommandFactory(
            generator_matrix_constants=Mock(spec=GeneratorMatrixConstants),
            matrix_service=Mock(spec=MatrixService),
            patch_service=Mock(spec=PatchService),
        )
        command_list = command_factory.to_icommand(command_dto=command_dto)
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
        command_factory.to_icommand(
            command_dto=CommandDTO(action="unknown_command", args={})
        )
