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

from pathlib import Path
from unittest.mock import Mock

from typing_extensions import override

from antarest.matrixstore.matrix_uri_mapper import MatrixStorageContext
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.lazy_node import LazyNode
from tests.storage.repository.filesystem.matrix.test_matrix_node import MockInputSeriesMatrix


class MockLazyNode(LazyNode[str, str, str]):
    def __init__(self, config: FileStudyTreeConfig) -> None:
        super().__init__(config=config)

    @override
    def load(
        self,
        url: list[str] | None = None,
        depth: int = -1,
        expanded: bool = False,
        formatted: bool = False,
    ) -> str:
        return "Mock Matrix Content"

    @override
    def dump(self, data: str, url: list[str] | None = None) -> None:
        self.config.path.write_text(data)

    def check_errors(self, data: str, url: list[str] | None = None, raising: bool = False) -> list[str]:
        pass  # not used


def test_get_no_expanded_txt(tmp_path: Path) -> None:
    file = tmp_path / "my-study/lazy.txt"
    file.parent.mkdir()
    file.touch()

    config = FileStudyTreeConfig(study_path=file, path=file, version=-1, study_id="my-study")

    node = MockLazyNode(config=config)
    assert "Mock Matrix Content" == node.get(expanded=False)


def test_get_expanded_txt(tmp_path: Path) -> None:
    file = tmp_path / "my-study/lazy.txt"
    file.parent.mkdir()
    file.touch()

    config = FileStudyTreeConfig(study_path=file, path=file, version=-1, study_id="my-study")

    node = MockLazyNode(config=config)
    assert "file://lazy.txt" == node.get(expanded=True)


def test_save_uri(tmp_path: Path) -> None:
    file = tmp_path / "my-study/lazy.txt"
    file.parent.mkdir()
    file.touch()

    matrix_service = Mock()
    matrix_service.exists.return_value = True

    matrix_mapper = MatrixStorageContext(matrix_service=matrix_service, is_managed=True)

    config = FileStudyTreeConfig(study_path=file, path=file, version=-1, study_id="")
    node = MockInputSeriesMatrix(matrix_storage_context=matrix_mapper, config=config)
    uri = "matrix://id"
    node.save(uri)
    assert (file.parent / f"{file.name}.link").read_text() == uri
    assert not file.exists()
    matrix_service.exists.assert_called_once_with("matrix://id")


def test_save_txt(tmp_path: Path) -> None:
    file = tmp_path / "my-study/lazy.txt"
    file.parent.mkdir()

    link = file.parent / f"{file.name}.link"
    link.touch()

    matrix_service = Mock()
    matrix_service.exists.return_value = True

    matrix_mapper = MatrixStorageContext(matrix_service=matrix_service, is_managed=True)

    config = FileStudyTreeConfig(study_path=file, path=file, version=-1, study_id="")
    node = MockInputSeriesMatrix(matrix_storage_context=matrix_mapper, config=config)

    content = "Mock File Content"
    node.save(content)
    assert (file.parent / f"{file.name}.link").read_text() == content
    # todo missing assert
