import re

import numpy as np
import pytest
from pydantic import ValidationError

from antarest.study.storage.rawstudy.model.filesystem.config.model import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.study_upgrader import upgrade_study
from antarest.study.storage.variantstudy.business.utils import strip_matrix_protocol
from antarest.study.storage.variantstudy.model.command.common import CommandName
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_st_storage import (
    REQUIRED_VERSION,
    CreateSTStorage,
    STStorageConfig,
)
from antarest.study.storage.variantstudy.model.command.replace_matrix import ReplaceMatrix
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from antarest.study.storage.variantstudy.model.model import CommandDTO


@pytest.fixture(name="recent_study")
def recent_study_fixture(empty_study: FileStudy) -> FileStudy:
    """
    Fixture for creating a recent version of the FileStudy object.

    Args:
        empty_study: The empty FileStudy object used as model.

    Returns:
        FileStudy: The FileStudy object upgraded to the required version.
    """
    upgrade_study(empty_study.config.study_path, str(REQUIRED_VERSION))
    empty_study.config.version = REQUIRED_VERSION
    return empty_study


# The parameter names to be used are those in the INI file.
# Non-string values are automatically converted into strings.
# noinspection SpellCheckingInspection
PARAMETERS = {
    "name": "Storage1",
    "group": "Battery",
    "injectionnominalcapacity": 1500,
    "withdrawalnominalcapacity": 1500,
    "reservoircapacity": 20000,
    "efficiency": 0.94,
    "initialleveloptim": True,
}

# noinspection SpellCheckingInspection
OTHER_PARAMETERS = {
    "name": "Storage1",
    "group": "Battery",
    "injectionnominalcapacity": 1200,
    "withdrawalnominalcapacity": 1300,
    "reservoircapacity": 20500,
    "efficiency": 0.92,
    "initiallevel": 0,
    "initialleveloptim": True,
}


class TestCreateSTStorage:
    # noinspection SpellCheckingInspection
    def test_init(self, command_context: CommandContext):
        pmax_injection = np.random.rand(8760, 1)
        inflows = np.random.uniform(0, 1000, size=(8760, 1))
        cmd = CreateSTStorage(
            command_context=command_context,
            area_id="area_fr",
            parameters=STStorageConfig(**PARAMETERS),
            pmax_injection=pmax_injection.tolist(),  # type: ignore
            inflows=inflows.tolist(),  # type: ignore
        )

        # Check the attribues
        assert cmd.command_name == CommandName.CREATE_ST_STORAGE
        assert cmd.version == 1
        assert cmd.command_context == command_context
        assert cmd.area_id == "area_fr"
        expected_parameters = {k: str(v) for k, v in PARAMETERS.items()}
        assert cmd.parameters == STStorageConfig(**expected_parameters)

        # check the matrices links
        
        constants = command_context.generator_matrix_constants
        assert cmd.pmax_injection != constants.get_st_storage_pmax_injection()
        assert cmd.pmax_withdrawal == constants.get_st_storage_pmax_withdrawal()
        assert cmd.lower_rule_curve == constants.get_st_storage_lower_rule_curve()
        assert cmd.upper_rule_curve == constants.get_st_storage_upper_rule_curve()
        assert cmd.inflows != constants.get_st_storage_inflows()
        

    def test_init__invalid_storage_name(
        self, recent_study: FileStudy, command_context: CommandContext
    ):
        # When we apply the config for a new ST Storage with a bad name
        with pytest.raises(ValidationError) as ctx:
            parameters = {**PARAMETERS, "name": "?%$$"}  # bad name
            CreateSTStorage(
                command_context=command_context,
                area_id="dummy",
                parameters=STStorageConfig(**parameters),
            )
        # We get 2 errors because the `storage_name` is duplicated in the `parameters`:
        assert ctx.value.errors() == [
            {
                "loc": ("__root__",),
                "msg": "Invalid short term storage name '?%$$'.",
                "type": "value_error",
            }
        ]

    # noinspection SpellCheckingInspection
    def test_init__invalid_matrix_values(
        self, command_context: CommandContext
    ):
        array = np.random.rand(8760, 1)  # OK
        array[10] = 25  # BAD
        with pytest.raises(ValidationError) as ctx:
            CreateSTStorage(
                command_context=command_context,
                area_id="area_fr",
                parameters=STStorageConfig(**PARAMETERS),
                pmax_injection=array.tolist(),  # type: ignore
            )
        assert ctx.value.errors() == [
            {
                "loc": ("pmax_injection",),
                "msg": "Matrix values should be between 0 and 1",
                "type": "value_error",
            }
        ]

    # noinspection SpellCheckingInspection
    def test_init__invalid_matrix_shape(self, command_context: CommandContext):
        array = np.random.rand(24, 1)  # BAD SHAPE
        with pytest.raises(ValidationError) as ctx:
            CreateSTStorage(
                command_context=command_context,
                area_id="area_fr",
                parameters=STStorageConfig(**PARAMETERS),
                pmax_injection=array.tolist(),  # type: ignore
            )
        assert ctx.value.errors() == [
            {
                "loc": ("pmax_injection",),
                "msg": "Invalid matrix shape (24, 1), expected (8760, 1)",
                "type": "value_error",
            }
        ]

        # noinspection SpellCheckingInspection

    def test_init__invalid_nan_value(self, command_context: CommandContext):
        array = np.random.rand(8760, 1)  # OK
        array[20] = np.nan  # BAD
        with pytest.raises(ValidationError) as ctx:
            CreateSTStorage(
                command_context=command_context,
                area_id="area_fr",
                parameters=STStorageConfig(**PARAMETERS),
                pmax_injection=array.tolist(),  # type: ignore
            )
        assert ctx.value.errors() == [
            {
                "loc": ("pmax_injection",),
                "msg": "Matrix values cannot contain NaN",
                "type": "value_error",
            }
        ]

        # noinspection SpellCheckingInspection

    def test_init__invalid_matrix_type(self, command_context: CommandContext):
        array = {"data": [1, 2, 3]}
        with pytest.raises(ValidationError) as ctx:
            CreateSTStorage(
                command_context=command_context,
                area_id="area_fr",
                parameters=STStorageConfig(**PARAMETERS),
                pmax_injection=array,  # type: ignore
            )
        assert ctx.value.errors() == [
            {
                "loc": ("pmax_injection",),
                "msg": "value is not a valid list",
                "type": "type_error.list",
            },
            {
                "loc": ("pmax_injection",),
                "msg": "str type expected",
                "type": "type_error.str",
            },
        ]

    def test_apply_config__invalid_version(
        self, empty_study: FileStudy, command_context: CommandContext
    ):
        # Given an old study in version 720
        # When we apply the config to add a new ST Storage
        create_st_storage = CreateSTStorage(
            command_context=command_context,
            area_id="foo",
            parameters=STStorageConfig(**PARAMETERS),
        )
        command_output = create_st_storage.apply_config(empty_study.config)

        # Then, the output should be an error
        assert command_output.status is False
        assert re.search(
            rf"Invalid.*version {empty_study.config.version}",
            command_output.message,
            flags=re.IGNORECASE,
        )

    def test_apply_config__missing_area(
        self, recent_study: FileStudy, command_context: CommandContext
    ):
        # Given a study without "unknown area" area
        # When we apply the config to add a new ST Storage
        create_st_storage = CreateSTStorage(
            command_context=command_context,
            area_id="unknown area",  # bad ID
            parameters=STStorageConfig(**PARAMETERS),
        )
        command_output = create_st_storage.apply_config(recent_study.config)

        # Then, the output should be an error
        assert command_output.status is False
        assert re.search(
            rf"'{re.escape(create_st_storage.area_id)}'.*does not exist",
            command_output.message,
            flags=re.IGNORECASE,
        )

    def test_apply_config__duplicate_storage(
        self, recent_study: FileStudy, command_context: CommandContext
    ):
        # First, prepare a new Area
        create_area = CreateArea(
            area_name="Area FR",
            command_context=command_context,
        )
        create_area.apply(recent_study)

        # Then, apply the config for a new ST Storage
        create_st_storage = CreateSTStorage(
            command_context=command_context,
            area_id=transform_name_to_id(create_area.area_name),
            parameters=STStorageConfig(**PARAMETERS),
        )
        command_output = create_st_storage.apply_config(recent_study.config)
        assert command_output.status is True

        # Then, apply the config a second time
        parameters = {**PARAMETERS, "name": "STORAGE1"}  # different case
        create_st_storage = CreateSTStorage(
            command_context=command_context,
            area_id=transform_name_to_id(create_area.area_name),
            parameters=STStorageConfig(**parameters),
        )
        command_output = create_st_storage.apply_config(recent_study.config)

        # Then, the output should be an error
        assert command_output.status is False
        assert re.search(
            rf"'{re.escape(create_st_storage.storage_name)}'.*already exists",
            command_output.message,
            flags=re.IGNORECASE,
        )

    def test_apply_config__nominal_case(
        self, recent_study: FileStudy, command_context: CommandContext
    ):
        # First, prepare a new Area
        create_area = CreateArea(
            area_name="Area FR",
            command_context=command_context,
        )
        create_area.apply(recent_study)

        # Then, apply the config for a new ST Storage
        create_st_storage = CreateSTStorage(
            command_context=command_context,
            area_id=transform_name_to_id(create_area.area_name),
            parameters=STStorageConfig(**PARAMETERS),
        )
        command_output = create_st_storage.apply_config(recent_study.config)

        # Check the command output and extra dict
        assert command_output.status is True
        assert re.search(
            rf"'{re.escape(create_st_storage.storage_name)}'.*added",
            command_output.message,
            flags=re.IGNORECASE,
        )

    # noinspection SpellCheckingInspection
    def test_apply__nominal_case(
        self, recent_study: FileStudy, command_context: CommandContext
    ):
        # First, prepare a new Area
        create_area = CreateArea(
            area_name="Area FR",
            command_context=command_context,
        )
        create_area.apply(recent_study)

        # Then, apply the command to create a new ST Storage
        pmax_injection = np.random.rand(8760, 1)
        inflows = np.random.uniform(0, 1000, size=(8760, 1))
        cmd = CreateSTStorage(
            command_context=command_context,
            area_id=transform_name_to_id(create_area.area_name),
            parameters=STStorageConfig(**PARAMETERS),
            pmax_injection=pmax_injection.tolist(),  # type: ignore
            inflows=inflows.tolist(),  # type: ignore
        )
        command_output = cmd.apply(recent_study)
        assert command_output.status

        # check the config
        config = recent_study.tree.get(
            ["input", "st-storage", "clusters", cmd.area_id, "list"]
        )
        expected = {
            "storage1": {
                "efficiency": 0.94,
                "group": "Battery",
                # "initiallevel": 0,  # default value is 0
                "initialleveloptim": True,
                "injectionnominalcapacity": 1500,
                "name": "Storage1",
                "reservoircapacity": 20000,
                "withdrawalnominalcapacity": 1500,
            }
        }
        assert config == expected

        # check the matrices references
        config = recent_study.tree.get(
            ["input", "st-storage", "series", cmd.area_id]
        )
        constants = command_context.generator_matrix_constants
        service = command_context.matrix_service
        pmax_injection_id = service.create(pmax_injection)
        inflows_id = service.create(inflows)
        expected = {
            "storage1": {
                "pmax_injection": f"matrix://{pmax_injection_id}",
                "pmax_withdrawal": constants.get_st_storage_pmax_withdrawal(),
                "lower_rule_curve": constants.get_st_storage_lower_rule_curve(),
                "upper_rule_curve": constants.get_st_storage_upper_rule_curve(),
                "inflows": f"matrix://{inflows_id}",
            }
        }
        assert config == expected

    def test_apply__invalid_apply_config(
        self, empty_study: FileStudy, command_context: CommandContext
    ):
        # First, prepare a new Area
        create_area = CreateArea(
            area_name="Area FR", command_context=command_context
        )
        create_area.apply(empty_study)

        # Then, apply the command to create a new ST Storage
        cmd = CreateSTStorage(
            command_context=command_context,
            area_id=transform_name_to_id(create_area.area_name),
            parameters=STStorageConfig(**PARAMETERS),
        )
        command_output = cmd.apply(empty_study)
        assert not command_output.status  # invalid study (too old)

    # noinspection SpellCheckingInspection
    def test_to_dto(self, command_context: CommandContext):
        cmd = CreateSTStorage(
            command_context=command_context,
            area_id="area_fr",
            parameters=STStorageConfig(**PARAMETERS),
        )

        actual = cmd.to_dto()

        expected_parameters = PARAMETERS.copy()
        # `initiallevel` = 0 because `initialleveloptim` is True
        expected_parameters["initiallevel"] = 0
        constants = command_context.generator_matrix_constants

        assert actual == CommandDTO(
            action=CommandName.CREATE_ST_STORAGE.value,
            args={
                "area_id": "area_fr",
                "parameters": expected_parameters,
                "pmax_injection": strip_matrix_protocol(
                    constants.get_st_storage_pmax_withdrawal()
                ),
                "pmax_withdrawal": strip_matrix_protocol(
                    constants.get_st_storage_pmax_withdrawal()
                ),
                "lower_rule_curve": strip_matrix_protocol(
                    constants.get_st_storage_lower_rule_curve()
                ),
                "upper_rule_curve": strip_matrix_protocol(
                    constants.get_st_storage_upper_rule_curve()
                ),
                "inflows": strip_matrix_protocol(
                    constants.get_st_storage_inflows()
                ),
            },
        )

    def test_match_signature(self, command_context: CommandContext):
        cmd = CreateSTStorage(
            command_context=command_context,
            area_id="area_fr",
            parameters=STStorageConfig(**PARAMETERS),
        )
        assert cmd.match_signature() == "create_st_storage%area_fr%storage1"

    @pytest.mark.parametrize("area_id", ["area_fr", "area_en"])
    @pytest.mark.parametrize("parameters", [PARAMETERS, OTHER_PARAMETERS])
    def test_match(
        self,
        command_context: CommandContext,
        area_id,
        parameters,
    ):
        cmd1 = CreateSTStorage(
            command_context=command_context,
            area_id="area_fr",
            parameters=STStorageConfig(**PARAMETERS),
        )
        cmd2 = CreateSTStorage(
            command_context=command_context,
            area_id=area_id,
            parameters=STStorageConfig(**parameters),
        )
        light_equal = (
            area_id == cmd1.area_id and parameters["name"] == cmd1.storage_name
        )
        assert cmd1.match(cmd2, equal=False) == light_equal
        deep_equal = area_id == cmd1.area_id and parameters == PARAMETERS
        assert cmd1.match(cmd2, equal=True) == deep_equal

    def test_match__unknown_type(self, command_context: CommandContext):
        cmd1 = CreateSTStorage(
            command_context=command_context,
            area_id="area_fr",
            parameters=STStorageConfig(**PARAMETERS),
        )
        # Always `False` when compared to another object type
        assert cmd1.match(..., equal=False) is False
        assert cmd1.match(..., equal=True) is False

    def test_create_diff__not_equals(self, command_context: CommandContext):
        cmd = CreateSTStorage(
            command_context=command_context,
            area_id="area_fr",
            parameters=STStorageConfig(**PARAMETERS),
        )
        upper_rule_curve = np.random.rand(8760, 1)
        inflows = np.random.uniform(0, 1000, size=(8760, 1))
        other = CreateSTStorage(
            command_context=command_context,
            area_id=cmd.area_id,
            parameters=STStorageConfig(**OTHER_PARAMETERS),
            upper_rule_curve=upper_rule_curve.tolist(),  # type: ignore
            inflows=inflows.tolist(),  # type: ignore
        )
        actual = cmd.create_diff(other)
        expected = [
            ReplaceMatrix(
                command_context=command_context,
                target="input/st-storage/series/area_fr/storage1/upper_rule_curve",
                matrix=strip_matrix_protocol(other.upper_rule_curve),
            ),
            ReplaceMatrix(
                command_context=command_context,
                target="input/st-storage/series/area_fr/storage1/inflows",
                matrix=strip_matrix_protocol(other.inflows),
            ),
            UpdateConfig(
                command_context=command_context,
                target="input/st-storage/clusters/area_fr/list/storage1",
                data=OTHER_PARAMETERS,
            ),
        ]
        assert actual == expected

    def test_create_diff__equals(self, command_context: CommandContext):
        cmd = CreateSTStorage(
            command_context=command_context,
            area_id="area_fr",
            parameters=STStorageConfig(**PARAMETERS),
        )
        actual = cmd.create_diff(cmd)
        assert not actual

    def test_get_inner_matrices(self, command_context: CommandContext):
        cmd = CreateSTStorage(
            command_context=command_context,
            area_id="area_fr",
            parameters=STStorageConfig(**PARAMETERS),
        )
        actual = cmd.get_inner_matrices()
        constants = command_context.generator_matrix_constants
        assert actual == [
            strip_matrix_protocol(constants.get_st_storage_pmax_injection()),
            strip_matrix_protocol(constants.get_st_storage_pmax_withdrawal()),
            strip_matrix_protocol(constants.get_st_storage_lower_rule_curve()),
            strip_matrix_protocol(constants.get_st_storage_upper_rule_curve()),
            strip_matrix_protocol(constants.get_st_storage_inflows()),
        ]
