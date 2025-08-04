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

from pathlib import Path
from typing import List, Optional
from unittest.mock import Mock

from antarest.matrixstore.matrix_uri_mapper import MatrixUriMapper, MatrixUriMapperManaged
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.lazy_node import LazyNode
from tests.storage.repository.filesystem.matrix.test_matrix_node import MockMatrixNode


class MockLazyNode(LazyNode[str, str, str]):
    def __init__(self, matrix_mapper: MatrixUriMapper, config: FileStudyTreeConfig) -> None:
        super().__init__(
            config=config,
            matrix_mapper=matrix_mapper,
        )

    def load(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
        formatted: bool = False,
    ) -> str:
        return "Mock Matrix Content"

    def dump(self, data: str, url: Optional[List[str]] = None) -> None:
        self.config.path.write_text(data)

    def check_errors(self, data: str, url: Optional[List[str]] = None, raising: bool = False) -> List[str]:
        pass  # not used


def test_get_no_expanded_txt(tmp_path: Path):
    file = tmp_path / "my-study/lazy.txt"
    file.parent.mkdir()
    file.touch()

    config = FileStudyTreeConfig(study_path=file, path=file, version=-1, study_id="my-study")

    node = MockLazyNode(
        matrix_mapper=Mock(),
        config=config,
    )
    assert "Mock Matrix Content" == node.get(expanded=False)


def test_get_expanded_txt(tmp_path: Path):
    file = tmp_path / "my-study/lazy.txt"
    file.parent.mkdir()
    file.touch()

    config = FileStudyTreeConfig(study_path=file, path=file, version=-1, study_id="my-study")

    node = MockLazyNode(
        matrix_mapper=Mock(),
        config=config,
    )
    assert "file://lazy.txt" == node.get(expanded=True)


def test_save_uri(tmp_path: Path):
    file = tmp_path / "my-study/lazy.txt"
    file.parent.mkdir()
    file.touch()

    matrix_service = Mock()
    matrix_service.exists.return_value = True

    matrix_mapper = MatrixUriMapperManaged(matrix_service)

    config = FileStudyTreeConfig(study_path=file, path=file, version=-1, study_id="")
    node = MockMatrixNode(matrix_mapper=matrix_mapper, config=config)

    uri = "matrix://id"
    node.save(uri)
    assert (file.parent / f"{file.name}.link").read_text() == uri
    assert not file.exists()
    matrix_service.exists.assert_called_once_with("id")


def test_save_txt(tmp_path: Path):
    file = tmp_path / "my-study/lazy.txt"
    file.parent.mkdir()

    link = file.parent / f"{file.name}.link"
    link.touch()

    matrix_service = Mock()
    matrix_service.exists.return_value = True

    matrix_mapper = MatrixUriMapperManaged(matrix_service)

    config = FileStudyTreeConfig(study_path=file, path=file, version=-1, study_id="")
    node = MockMatrixNode(matrix_mapper=matrix_mapper, config=config)

    content = "Mock File Content"
    node.save(content)
    assert (file.parent / f"{file.name}.link").read_text() == content
    # todo missing assert
