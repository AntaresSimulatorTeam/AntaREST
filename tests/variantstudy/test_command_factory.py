from unittest.mock import Mock

import pytest

from antarest.study.storage.variantstudy.command_factory import CommandFactory
from antarest.study.storage.variantstudy.model import CommandDTO
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
            action=CommandName.UPDATE_AREA.value,
            args={"id": "id", "name": "name", "metadata": {}},
        ),
        CommandDTO(
            action=CommandName.UPDATE_AREA.value,
            args=[{"id": "id", "name": "name", "metadata": {}}],
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
            args={"id": "id", "metadata": {}},
        ),
        CommandDTO(
            action=CommandName.CREATE_DISTRICT.value,
            args=[{"id": "id", "metadata": {}}],
        ),
        CommandDTO(
            action=CommandName.UPDATE_DISTRICT.value,
            args={"id": "id", "name": "name", "metadata": {}, "set": []},
        ),
        CommandDTO(
            action=CommandName.UPDATE_DISTRICT.value,
            args=[{"id": "id", "name": "name", "metadata": {}, "set": []}],
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
            action=CommandName.UPDATE_LINK.value,
            args={
                "id": "id",
                "name": "name",
                "parameters": {},
                "series": "series",
            },
        ),
        CommandDTO(
            action=CommandName.UPDATE_LINK.value,
            args=[
                {
                    "id": "id",
                    "name": "name",
                    "parameters": {},
                    "series": "series",
                }
            ],
        ),
        CommandDTO(
            action=CommandName.REMOVE_LINK.value,
            args={"id": "id"},
        ),
        CommandDTO(
            action=CommandName.REMOVE_LINK.value,
            args=[{"id": "id"}],
        ),
        CommandDTO(
            action=CommandName.CREATE_BINDING_CONSTRAINT.value,
            args={
                "name": "name",
                "enabled": True,
                "time_step": "hourly",
                "operator": "equal",
                "coeffs": [],
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
                    "coeffs": [],
                    "values": "values",
                }
            ],
        ),
        CommandDTO(
            action=CommandName.UPDATE_BINDING_CONSTRAINT.value,
            args={
                "id": "id",
                "name": "name",
                "enabled": True,
                "time_step": "hourly",
                "operator": "equal",
                "coeffs": [],
                "values": "values",
            },
        ),
        CommandDTO(
            action=CommandName.UPDATE_BINDING_CONSTRAINT.value,
            args=[
                {
                    "id": "id",
                    "name": "name",
                    "enabled": True,
                    "time_step": "hourly",
                    "operator": "equal",
                    "coeffs": [],
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
                "name": "name",
                "type": "type",
                "parameters": {},
                "prepro": "prepro",
                "modulation": "modulation",
            },
        ),
        CommandDTO(
            action=CommandName.CREATE_CLUSTER.value,
            args=[
                {
                    "name": "name",
                    "type": "type",
                    "parameters": {},
                    "prepro": "prepro",
                    "modulation": "modulation",
                }
            ],
        ),
        CommandDTO(
            action=CommandName.UPDATE_CLUSTER.value,
            args={
                "id": "id",
                "name": "name",
                "type": "type",
                "parameters": {},
                "prepro": "prepro",
                "modulation": "modulation",
            },
        ),
        CommandDTO(
            action=CommandName.UPDATE_CLUSTER.value,
            args=[
                {
                    "id": "id",
                    "name": "name",
                    "type": "type",
                    "parameters": {},
                    "prepro": "prepro",
                    "modulation": "modulation",
                }
            ],
        ),
        CommandDTO(
            action=CommandName.REMOVE_CLUSTER.value,
            args={"id": "id"},
        ),
        CommandDTO(
            action=CommandName.REMOVE_CLUSTER.value,
            args=[{"id": "id"}],
        ),
        CommandDTO(
            action=CommandName.REPLACE_MATRIX.value,
            args={"target_element": "target_element", "matrix": "matrix"},
        ),
        CommandDTO(
            action=CommandName.REPLACE_MATRIX.value,
            args=[{"target_element": "target_element", "matrix": "matrix"}],
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
        generator_matrix_constants=Mock(), matrix_service=Mock()
    )
    command_list = command_factory.to_icommand(command_dto=command_dto)
    if isinstance(args := command_dto.args, dict):
        assert len(command_list) == 1
    else:
        assert len(command_list) == len(args)

    for command in command_list:
        assert command.command_name.value == command_dto.action


@pytest.mark.unit_test
def test_unknown_command():
    with pytest.raises(NotImplementedError):
        command_factory = CommandFactory(
            generator_matrix_constants=Mock(), matrix_service=Mock()
        )
        command_factory.to_icommand(
            command_dto=CommandDTO(action="unknown_command", args={})
        )
