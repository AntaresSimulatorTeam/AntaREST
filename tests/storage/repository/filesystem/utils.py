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
from zipfile import ZipFile

from antarest.matrixstore.uri_resolver_service import MatrixUriMapper
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE, INode


class CheckSubNode(INode[int, int, int]):
    def normalize(self) -> None:
        pass

    def denormalize(self) -> None:
        pass

    def build(self, config: FileStudyTreeConfig) -> "TREE":
        pass

    def __init__(self, config: FileStudyTreeConfig, value: int):
        super().__init__(config)
        self.value = value

    def get_node(
        self,
        url: Optional[List[str]] = None,
    ) -> INode[int, int, int]:
        return self

    def get(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = True,
        formatted: bool = True,
    ) -> int:
        return self.value

    def save(self, data: int, url: Optional[List[str]] = None) -> None:
        self.value = data

    def delete(self, url: Optional[List[str]] = None) -> None:
        pass

    def check_errors(self, data: int, url: Optional[List[str]] = None, raising: bool = False) -> List[str]:
        return []


class TestMiddleNode(FolderNode):
    def __init__(
        self,
        matrix_mapper: MatrixUriMapper,
        config: FileStudyTreeConfig,
        children: TREE,
    ):
        super().__init__(matrix_mapper, config)
        self.children = children

    def build(self) -> TREE:
        return self.children


def extract_sta(project_path: Path, tmp_path: Path) -> Path:
    with ZipFile(project_path / "examples/studies/STA-mini.zip") as zip_output:
        zip_output.extractall(path=tmp_path / "studies")

    return tmp_path / "studies/STA-mini"
