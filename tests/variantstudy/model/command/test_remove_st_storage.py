# Copyright (c) 2025, RTE (https://www.rte-france.com)
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

import re

import pytest
from pydantic import ValidationError

from antarest.study.model import STUDY_VERSION_8_8
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.study_upgrader import StudyUpgrader
from antarest.study.storage.variantstudy.model.command.common import CommandName
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_st_storage import CreateSTStorage
from antarest.study.storage.variantstudy.model.command.remove_st_storage import REQUIRED_VERSION, RemoveSTStorage
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
    StudyUpgrader(empty_study.config.study_path, str(REQUIRED_VERSION)).upgrade()
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


class TestRemoveSTStorage:
    # noinspection SpellCheckingInspection
    def test_init(self, command_context: CommandContext):
        cmd = RemoveSTStorage(
            command_context=command_context, area_id="area_fr", storage_id="storage_1", study_version=STUDY_VERSION_8_8
        )

        # Check the attribues
        assert cmd.command_name == CommandName.REMOVE_ST_STORAGE
        assert cmd.study_version == STUDY_VERSION_8_8
        assert cmd.command_context == command_context
        assert cmd.area_id == "area_fr"
        assert cmd.storage_id == "storage_1"

    def test_init__invalid_storage_id(self, recent_study: FileStudy, command_context: CommandContext):
        # When we apply the config for a new ST Storage with a bad name
        with pytest.raises(ValidationError) as ctx:
            RemoveSTStorage(
                command_context=command_context,
                area_id="dummy",
                storage_id="?%$$",  # bad name
                study_version=STUDY_VERSION_8_8,
            )
        assert ctx.value.errors() == [
            {
                "ctx": {"pattern": "[a-z0-9_(),& -]+"},
                "input": "?%$$",
                "loc": ("storage_id",),
                "msg": "String should match pattern '[a-z0-9_(),& -]+'",
                "type": "string_pattern_mismatch",
                "url": "https://errors.pydantic.dev/2.10/v/string_pattern_mismatch",
            }
        ]

    def test_apply_config__invalid_version(self, empty_study: FileStudy, command_context: CommandContext):
        # Given an old study in version 720
        study_version = empty_study.config.version
        # When we apply the config to add a new ST Storage
        remove_st_storage = RemoveSTStorage(
            command_context=command_context, area_id="foo", storage_id="bar", study_version=study_version
        )
        command_output = remove_st_storage.apply_config(empty_study.config)

        # Then, the output should be an error
        assert command_output.status is False
        assert re.search(
            rf"Invalid.*version {study_version}",
            command_output.message,
            flags=re.IGNORECASE,
        )

    def test_apply_config__missing_area(self, recent_study: FileStudy, command_context: CommandContext):
        # Given a study without "unknown area" area
        # When we apply the config to add a new ST Storage
        remove_st_storage = RemoveSTStorage(
            command_context=command_context,
            area_id="unknown area",  # bad ID
            storage_id="storage_1",
            study_version=recent_study.config.version,
        )
        command_output = remove_st_storage.apply_config(recent_study.config)

        # Then, the output should be an error
        assert command_output.status is False
        assert re.search(
            rf"'{re.escape(remove_st_storage.area_id)}'.*does not exist",
            command_output.message,
            flags=re.IGNORECASE,
        )

    def test_apply_config__missing_storage(self, recent_study: FileStudy, command_context: CommandContext):
        # First, prepare a new Area
        create_area = CreateArea(
            command_context=command_context, area_name="Area FR", study_version=recent_study.config.version
        )
        create_area.apply(recent_study)

        # Then, apply the config for a new ST Storage
        remove_st_storage = RemoveSTStorage(
            command_context=command_context,
            area_id=transform_name_to_id(create_area.area_name),
            storage_id="storage 1",
            study_version=recent_study.config.version,
        )
        command_output = remove_st_storage.apply_config(recent_study.config)

        # Then, the output should be an error
        assert command_output.status is False
        assert re.search(
            rf"'{re.escape(remove_st_storage.storage_id)}'.*does not exist",
            command_output.message,
            flags=re.IGNORECASE,
        )

    def test_apply_config__nominal_case(self, recent_study: FileStudy, command_context: CommandContext):
        study_version = recent_study.config.version
        # First, prepare a new Area
        create_area = CreateArea(area_name="Area FR", command_context=command_context, study_version=study_version)
        create_area.apply(recent_study)

        # Then, prepare a new Storage
        create_st_storage = CreateSTStorage(
            command_context=command_context,
            area_id=transform_name_to_id(create_area.area_name),
            parameters=PARAMETERS,  # type: ignore
            study_version=study_version,
        )
        create_st_storage.apply(recent_study)

        # Then, apply the config for a new ST Storage
        remove_st_storage = RemoveSTStorage(
            command_context=command_context,
            area_id=transform_name_to_id(create_area.area_name),
            storage_id=create_st_storage.storage_id,
            study_version=study_version,
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
            command_context=command_context, area_id="area_fr", storage_id="storage_1", study_version=STUDY_VERSION_8_8
        )
        actual = cmd.to_dto()

        # noinspection SpellCheckingInspection
        assert actual == CommandDTO(
            action=CommandName.REMOVE_ST_STORAGE.value,
            args={"area_id": "area_fr", "storage_id": "storage_1"},
            study_version=STUDY_VERSION_8_8,
        )

    def test_get_inner_matrices(self, command_context: CommandContext):
        cmd = RemoveSTStorage(
            command_context=command_context, area_id="area_fr", storage_id="storage_1", study_version=STUDY_VERSION_8_8
        )
        actual = cmd.get_inner_matrices()
        assert actual == []
