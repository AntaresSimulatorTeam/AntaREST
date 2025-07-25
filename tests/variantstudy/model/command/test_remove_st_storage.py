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


import pytest
from pydantic import ValidationError

from antarest.study.model import STUDY_VERSION_8_8
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.study_upgrader import StudyUpgrader
from antarest.study.storage.variantstudy.model.command.common import CommandName
from antarest.study.storage.variantstudy.model.command.remove_st_storage import REQUIRED_VERSION, RemoveSTStorage
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from antarest.study.storage.variantstudy.model.model import CommandDTO


@pytest.fixture(name="recent_study")
def recent_study_fixture(empty_study_720: FileStudy) -> FileStudy:
    """
    Fixture for creating a recent version of the FileStudy object.

    Args:
        empty_study: The empty FileStudy object used as model.

    Returns:
        FileStudy: The FileStudy object upgraded to the required version.
    """
    StudyUpgrader(empty_study_720.config.study_path, str(REQUIRED_VERSION)).upgrade()
    empty_study_720.config.version = REQUIRED_VERSION
    return empty_study_720


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

        errors = ctx.value.errors()
        for error in errors:
            error.pop("url", None)

        assert errors == [
            {
                "ctx": {"pattern": "[a-z0-9_(),& -]+"},
                "input": "?%$$",
                "loc": ("storage_id",),
                "msg": "String should match pattern '[a-z0-9_(),& -]+'",
                "type": "string_pattern_mismatch",
            }
        ]

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
