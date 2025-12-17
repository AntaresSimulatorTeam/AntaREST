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
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Generic, List, Optional, Tuple
from zipfile import ZipFile

from typing_extensions import override

from antarest.matrixstore.matrix_uri_mapper import MatrixUriMapper
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.inode import G, INode, S, V


class LazyNode(INode, ABC, Generic[G, S, V]):  # type: ignore
    """
    A "lazy" node does not return its full content but a summarized, short representation
    when in the context of a tree expansion (typically getting children of a folder node).
    """

    def __init__(
        self,
        matrix_mapper: MatrixUriMapper,
        config: FileStudyTreeConfig,
    ) -> None:
        self.matrix_mapper = matrix_mapper
        super().__init__(config)

    def _get_real_file_path(
        self,
    ) -> Tuple[Path, Any]:
        tmp_dir = None
        if self.config.archive_path:
            path, tmp_dir = self._extract_file_to_tmp_dir(self.config.archive_path)
        else:
            path = self.config.path
        return path, tmp_dir

    def file_exists(self) -> bool:
        if self.config.archive_path:
            str_zipped_path = str(self.config.archive_path)
            inside_zip_path = str(self.config.path)[len(str_zipped_path[:-4]) + 1 :]
            str_inside_zip_path = str(inside_zip_path).replace("\\", "/")
            with ZipFile(file=self.config.archive_path) as zip_file:
                file_names = zip_file.namelist()
            return str_inside_zip_path in file_names
        else:
            return self.config.path.exists()

    @override
    def get(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
        formatted: bool = True,
    ) -> str | G:
        if expanded:
            return self.get_lazy_content()

        return self.load(url, depth, expanded, formatted)

    @override
    def get_node_and_remainder(
        self,
        url: Optional[List[str]] = None,
    ) -> tuple[INode[G, S, V], list[str]]:
        self._assert_url_end(url)
        return self, []

    @override
    def delete(self, url: Optional[List[str]] = None) -> None:
        self._assert_url_end(url)
        if self.config.path.exists():
            self.config.path.unlink()

    @override
    def save(self, data: S, url: Optional[List[str]] = None) -> None:
        self._assert_not_in_zipped_file()
        self._assert_url_end(url)
        self.dump(data, url)

    def get_lazy_content(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
    ) -> str:
        return f"file://{self.config.path.name}"

    @abstractmethod
    def load(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
        formatted: bool = True,
    ) -> G:
        """
        Fetch data on disk.

        Args:
            url: data path to retrieve
            depth: after url is reached, node expand tree until matches depth asked
            expanded: context parameter to determine if current node comes from an expansion
            formatted: ask for raw file transformation

        Returns:

        """
        raise NotImplementedError()

    @abstractmethod
    def dump(self, data: S, url: Optional[List[str]] = None) -> None:
        """
        Store data on tree.

        Args:
            data: new data to save
            url: data path to change

        Returns:

        """
        raise NotImplementedError()
