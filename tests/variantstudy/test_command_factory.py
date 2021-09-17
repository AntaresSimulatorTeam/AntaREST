from unittest.mock import Mock

import pytest

from antarest.matrixstore.service import MatrixService
from antarest.study.storage.variantstudy.business.matrix_constants_generator import (
    GeneratorMatrixConstants,
)
from antarest.study.storage.variantstudy.command_factory import CommandFactory
from antarest.study.storage.variantstudy.model.command.utils import (
    remove_none_args,
)
from antarest.study.storage.variantstudy.model.model import CommandDTO
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
)


@pytest.mark.parametrize(
    "command_dto",
    [
        CommandDTO(
            action=CommandName.CREATE_AREA.value,
            args={"area_name": "area_name", "metadata": {}},
        ),
        CommandDTO(
            action=CommandName.CREATE_AREA.value,
            args=[
                {"area_name": "area_name", "metadata": {}},
                {"area_name": "area2", "metadata": {}},
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
            args={"name": "id", "metadata": {}, "filter_items": ["a"]},
        ),
        CommandDTO(
            action=CommandName.CREATE_DISTRICT.value,
            args=[{"name": "id", "metadata": {}, "base_filter": "add-all"}],
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
    ],
)
@pytest.mark.unit_test
def test_command_factory(command_dto: CommandDTO):
    command_factory = CommandFactory(
        generator_matrix_constants=Mock(spec=GeneratorMatrixConstants),
        matrix_service=Mock(spec=MatrixService),
    )
    command_list = command_factory.to_icommand(command_dto=command_dto)
    if isinstance(args := command_dto.args, dict):
        assert len(command_list) == 1
        assert remove_none_args(command_list[0].to_dto()) == command_dto
    else:
        assert len(command_list) == len(args)

    for command in command_list:
        assert command.command_name.value == command_dto.action


@pytest.mark.unit_test
def test_unknown_command():
    with pytest.raises(NotImplementedError):
        command_factory = CommandFactory(
            generator_matrix_constants=Mock(spec=GeneratorMatrixConstants),
            matrix_service=Mock(spec=MatrixService),
        )
        command_factory.to_icommand(
            command_dto=CommandDTO(action="unknown_command", args={})
        )
