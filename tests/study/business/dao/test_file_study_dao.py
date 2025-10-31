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
from pathlib import Path, PurePosixPath

from antarest.study.business.model.link_model import Link
from antarest.study.business.model.user_model import ResourceType, UserResourceDataCreation
from antarest.study.dao.file.file_study_dao import FileStudyTreeDao
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command_context import CommandContext


def test_file_study_dao(tmp_path: Path, empty_study_930: FileStudy, command_context: CommandContext) -> None:
    dao = FileStudyTreeDao(empty_study_930, command_context.generator_matrix_constants, command_context.blob_service)
    # Create 2 areas, 1 link, an Xpansion configuration and several user resources
    dao.create_xpansion_configuration()
    dao.save_area("FR")
    dao.save_area("de")
    dao.save_link(Link(area1="fr", area2="de"))
    blob_id1 = command_context.blob_service.save(b"Usain Bolt")
    path1 = PurePosixPath("file1.txt")
    dao.save_user_resource(UserResourceDataCreation(path=path1, resource_type=ResourceType.FILE, blob_id=blob_id1))
    blob_id2 = command_context.blob_service.save(b"Gout Gout")
    path2 = PurePosixPath("folder_1/file2.txt")
    dao.save_user_resource(UserResourceDataCreation(path=path2, resource_type=ResourceType.FILE, blob_id=blob_id2))

    # Tests link matrices

    # Tests hydro matrices

    # Tests user resources
    user_path = empty_study_930.config.study_path / "user"
    user_resources = sorted(dao.get_all_user_resources(), key=lambda res: res.path)
    assert len(user_resources) == 2
    res1 = user_resources[0]
    assert res1.path.as_posix() == str(user_path / path1)
    assert res1.blob_id == blob_id1

    res2 = user_resources[1]
    assert res2.path.as_posix() == str(user_path / path2)
    assert res2.blob_id == blob_id2
