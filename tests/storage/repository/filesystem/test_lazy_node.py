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

from antarest.matrixstore.uri_resolver_service import MatrixUriMapper
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.lazy_node import LazyNode


class MockLazyNode(LazyNode[str, str, str]):
    def normalize(self) -> None:
        pass  # no external store in this node

    def denormalize(self) -> None:
        pass  # no external store in this node

    def __init__(self, context: MatrixUriMapper, config: FileStudyTreeConfig) -> None:
        super().__init__(
            config=config,
            context=context,
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
        context=Mock(),
        config=config,
    )
    assert "Mock Matrix Content" == node.get(expanded=False)


def test_get_expanded_txt(tmp_path: Path):
    file = tmp_path / "my-study/lazy.txt"
    file.parent.mkdir()
    file.touch()

    config = FileStudyTreeConfig(study_path=file, path=file, version=-1, study_id="my-study")

    node = MockLazyNode(
        context=Mock(),
        config=config,
    )
    assert "file://lazy.txt" == node.get(expanded=True)


def test_get_expanded_link(tmp_path: Path):
    uri = "matrix://my-link"

    file = tmp_path / "my-study/lazy.txt"
    file.parent.mkdir()
    (file.parent / "lazy.txt.link").write_text(uri)

    config = FileStudyTreeConfig(study_path=file, path=file, version=-1, study_id="my-study")

    node = MockLazyNode(
        context=Mock(),
        config=config,
    )
    assert uri == node.get(expanded=True)


def test_save_uri(tmp_path: Path):
    file = tmp_path / "my-study/lazy.txt"
    file.parent.mkdir()
    file.touch()

    resolver = Mock()
    resolver.matrix_exists.return_value = True

    config = FileStudyTreeConfig(study_path=file, path=file, version=-1, study_id="")
    node = MockLazyNode(context=resolver, config=config)

    uri = "matrix://id"
    node.save(uri)
    assert (file.parent / f"{file.name}.link").read_text() == uri
    assert not file.exists()
    resolver.matrix_exists.assert_called_once_with(uri)


def test_save_txt(tmp_path: Path):
    file = tmp_path / "my-study/lazy.txt"
    file.parent.mkdir()

    link = file.parent / f"{file.name}.link"
    link.touch()

    resolver = Mock()
    resolver.matrix_exists.return_value = False

    config = FileStudyTreeConfig(study_path=file, path=file, version=-1, study_id="")
    node = MockLazyNode(context=resolver, config=config)

    content = "Mock File Content"
    node.save(content)
    assert file.read_text() == content
    assert not link.exists()
    resolver.matrix_exists.assert_called_once_with(content)
