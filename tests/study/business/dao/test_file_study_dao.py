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

import pandas as pd

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
    matrix1 = pd.DataFrame([[1, 2], [3, 4]])
    matrix2 = pd.DataFrame([[5, 6], [7, 8]])
    matrix3 = pd.DataFrame([[9, 10], [11, 12]])

    series_id_1 = command_context.matrix_service.create(matrix1)
    series_id_2 = command_context.matrix_service.create(matrix2)
    series_id_3 = command_context.matrix_service.create(matrix3)

    dao.save_link_series("de", "fr", series_id_1)
    dao.save_link_direct_capacities("fr", "de", series_id_2)
    dao.save_link_indirect_capacities("de", "fr", series_id_3)

    assert dao.get_link_series("de", "fr").equals(matrix1)
    assert dao.get_link_direct_capacities("de", "fr").equals(matrix2)
    assert dao.get_link_indirect_capacities("de", "fr").equals(matrix3)

    # Tests user resources
    user_resources = sorted(dao.get_all_user_resources(), key=lambda res: res.path)
    assert len(user_resources) == 2
    res1 = user_resources[0]
    assert res1.path.as_posix() == str(path1)  # Ensures the path is relative to the `user` folder
    assert res1.blob_id == blob_id1

    res2 = user_resources[1]
    assert res2.path.as_posix() == str(path2)
    assert res2.blob_id == blob_id2
