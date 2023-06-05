import re

import pytest
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    transform_name_to_id,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.study_upgrader import upgrade_study
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.create_area import (
    CreateArea,
)
from antarest.study.storage.variantstudy.model.command.create_st_storage import (
    CreateSTStorage,
)
from antarest.study.storage.variantstudy.model.command.remove_st_storage import (
    REQUIRED_VERSION,
    RemoveSTStorage,
)
from antarest.study.storage.variantstudy.model.command_context import (
    CommandContext,
)
from antarest.study.storage.variantstudy.model.model import CommandDTO
from pydantic import ValidationError


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
    "group": "Battery",
    "injectionnominalcapacity": 1500,
    "withdrawalnominalcapacity": 1500,
    "reservoircapacity": 20000,
    "efficiency": 0.94,
    "initialleveloptim": True,
}


class TestRemoveSTStorage:
    # noinspection SpellCheckingInspection
    def test_init(self, command_context: CommandContext):
        cmd = RemoveSTStorage(
            command_context=command_context,
            area_id="area_fr",
            storage_id="storage_1",
        )

        # Check the attribues
        assert cmd.command_name == CommandName.REMOVE_ST_STORAGE
        assert cmd.version == 1
        assert cmd.command_context == command_context
        assert cmd.area_id == "area_fr"
        assert cmd.storage_id == "storage_1"

    def test_init__invalid_storage_id(
        self, recent_study: FileStudy, command_context: CommandContext
    ):
        # When we apply the config for a new ST Storage with a bad name
        with pytest.raises(ValidationError) as ctx:
            RemoveSTStorage(
                command_context=command_context,
                area_id="dummy",
                storage_id="?%$$",  # bad name
            )
        assert ctx.value.errors() == [
            {
                "ctx": {"pattern": "[a-z0-9_(),& -]+"},
                "loc": ("storage_id",),
                "msg": 'string does not match regex "[a-z0-9_(),& -]+"',
                "type": "value_error.str.regex",
            }
        ]

    def test_apply_config__invalid_version(
        self, empty_study: FileStudy, command_context: CommandContext
    ):
        # Given an old study in version 720
        # When we apply the config to add a new ST Storage
        remove_st_storage = RemoveSTStorage(
            command_context=command_context,
            area_id="foo",
            storage_id="bar",
        )
        command_output = remove_st_storage.apply_config(empty_study.config)

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
        remove_st_storage = RemoveSTStorage(
            command_context=command_context,
            area_id="unknown area",  # bad ID
            storage_id="storage_1",
        )
        command_output = remove_st_storage.apply_config(recent_study.config)

        # Then, the output should be an error
        assert command_output.status is False
        assert re.search(
            rf"'{re.escape(remove_st_storage.area_id)}'.*does not exist",
            command_output.message,
            flags=re.IGNORECASE,
        )

    def test_apply_config__missing_storage(
        self, recent_study: FileStudy, command_context: CommandContext
    ):
        # First, prepare a new Area
        create_area = CreateArea(
            command_context=command_context,
            area_name="Area FR",
        )
        create_area.apply(recent_study)

        # Then, apply the config for a new ST Storage
        remove_st_storage = RemoveSTStorage(
            command_context=command_context,
            area_id=transform_name_to_id(create_area.area_name),
            storage_id="storage 1",
        )
        command_output = remove_st_storage.apply_config(recent_study.config)

        # Then, the output should be an error
        assert command_output.status is False
        assert re.search(
            rf"'{re.escape(remove_st_storage.storage_id)}'.*does not exist",
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

        # Then, prepare a new Storage
        create_st_storage = CreateSTStorage(
            command_context=command_context,
            area_id=transform_name_to_id(create_area.area_name),
            storage_name="Storage1",
            parameters=PARAMETERS,
        )
        create_st_storage.apply(recent_study)

        # Then, apply the config for a new ST Storage
        remove_st_storage = RemoveSTStorage(
            command_context=command_context,
            area_id=transform_name_to_id(create_area.area_name),
            storage_id=create_st_storage.storage_id,
        )
        command_output = remove_st_storage.apply_config(recent_study.config)

        # Check the command output and extra dict
        assert command_output.status is True
        assert re.search(
            rf"'{re.escape(remove_st_storage.storage_id)}'.*removed",
            command_output.message,
            flags=re.IGNORECASE,
        )

    def test_to_dto(self, command_context: CommandContext):
        cmd = RemoveSTStorage(
            command_context=command_context,
            area_id="area_fr",
            storage_id="storage_1",
        )
        actual = cmd.to_dto()

        # noinspection SpellCheckingInspection
        assert actual == CommandDTO(
            action=CommandName.REMOVE_ST_STORAGE.value,
            args={"area_id": "area_fr", "storage_id": "storage_1"},
        )

    def test_match_signature(self, command_context: CommandContext):
        cmd = RemoveSTStorage(
            command_context=command_context,
            area_id="area_fr",
            storage_id="storage_1",
        )
        assert cmd.match_signature() == "remove_st_storage%area_fr%storage_1"

    @pytest.mark.parametrize("area_id", ["area_fr", "area_en"])
    @pytest.mark.parametrize("storage_id", ["storage_1", "storage_2"])
    def test_match(
        self,
        command_context: CommandContext,
        area_id,
        storage_id,
    ):
        cmd1 = RemoveSTStorage(
            command_context=command_context,
            area_id="area_fr",
            storage_id="storage_1",
        )
        cmd2 = RemoveSTStorage(
            command_context=command_context,
            area_id=area_id,
            storage_id=storage_id,
        )
        is_equal = area_id == cmd1.area_id and storage_id == cmd1.storage_id
        assert cmd1.match(cmd2, equal=False) == is_equal
        assert cmd1.match(cmd2, equal=True) == is_equal

    def test_create_diff(self, command_context: CommandContext):
        cmd = RemoveSTStorage(
            command_context=command_context,
            area_id="area_fr",
            storage_id="storage_1",
        )
        other = RemoveSTStorage(
            command_context=command_context,
            area_id=cmd.area_id,
            storage_id=cmd.storage_id,
        )
        actual = cmd.create_diff(other)
        assert not actual

    def test_get_inner_matrices(self, command_context: CommandContext):
        cmd = RemoveSTStorage(
            command_context=command_context,
            area_id="area_fr",
            storage_id="storage_1",
        )
        actual = cmd.get_inner_matrices()
        assert actual == []
