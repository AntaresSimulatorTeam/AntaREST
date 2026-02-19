# Copyright (c) 2026, RTE (https://www.rte-france.com)
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
from pathlib import PurePosixPath

import pytest

from antarest.study.business.model.user_model import ResourceType, UserResourceDataCreation
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.replace_user_resource import ReplaceUserResource
from antarest.study.storage.variantstudy.model.command_context import CommandContext


def _set_up(command_context: CommandContext) -> list[str]:
    # Creates several files in the blob store
    blob_1 = command_context.blob_service.save(b"Hello World !")
    blob_2 = command_context.blob_service.save(b"Thunder Nuggets")
    blob_3 = command_context.blob_service.save(b"1.0,2.3\t4.5,6.7\t")
    return [blob_1, blob_2, blob_3]


def test_nominal_case(empty_study_930: FileStudy, command_context: CommandContext) -> None:
    study = empty_study_930
    blob_ids = _set_up(command_context)

    cmd = ReplaceUserResource(
        data=UserResourceDataCreation(
            path=PurePosixPath("new_file.txt"),
            resource_type=ResourceType.FILE,
            blob_id=blob_ids[0],
        ),
        command_context=command_context,
        study_version=study.config.version,
    )
    output = cmd.apply(study)
    assert output.status

    # Checks the right file was written in the study.
    content = study.tree.get(["user", "new_file.txt"])
    assert content == b"Hello World !"

    cmd = ReplaceUserResource(
        data=UserResourceDataCreation(
            path=PurePosixPath("new_folder/second_folder"),
            resource_type=ResourceType.FOLDER,
        ),
        command_context=command_context,
        study_version=study.config.version,
    )
    output = cmd.apply(study)
    assert output.status

    # Checks the folder was created in the study.
    content = study.tree.get(["user", "new_folder"])
    assert content == {"second_folder": {}}


def test_error_case(empty_study_930: FileStudy, command_context: CommandContext) -> None:
    study = empty_study_930
    _set_up(command_context)

    # Unexisting blob_id

    cmd = ReplaceUserResource(
        data=UserResourceDataCreation(
            path=PurePosixPath("new_file.txt"),
            resource_type=ResourceType.FILE,
            blob_id="fake_id",
        ),
        command_context=command_context,
        study_version=study.config.version,
    )
    output = cmd.apply(study)
    assert not output.status
    assert "'fake_id'" in output.message

    # Giving a blob_id with a resource_type.FOLDER

    with pytest.raises(ValueError, match="You cannot provide a blob_id for a folder"):
        UserResourceDataCreation(
            path=PurePosixPath("new_file.txt"),
            resource_type=ResourceType.FOLDER,
            blob_id="blob_id",
        )
