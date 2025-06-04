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
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Generic, List, Optional, Tuple, cast
from zipfile import ZipFile

from typing_extensions import override

from antarest.matrixstore.matrix_uri_mapper import MatrixUriMapper, MatrixUriMapperManaged
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.inode import G, INode, S, V


@dataclass
class SimpleCache:
    value: Any
    expiration_date: datetime


class LazyNode(INode, ABC, Generic[G, S, V]):  # type: ignore
    """
    Abstract left with implemented a lazy loading for its daughter implementation.
    """

    ZIP_FILELIST_CACHE: Dict[str, SimpleCache] = {}

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
            link_path = self.get_link_path()
            path = link_path if link_path.exists() else self.config.path
        return path, tmp_dir

    def file_exists(self) -> bool:
        if self.config.archive_path:
            str_zipped_path = str(self.config.archive_path)
            inside_zip_path = str(self.config.path)[len(str_zipped_path[:-4]) + 1 :]
            str_inside_zip_path = str(inside_zip_path).replace("\\", "/")
            if str_zipped_path not in LazyNode.ZIP_FILELIST_CACHE:
                with ZipFile(file=self.config.archive_path) as zip_file:
                    LazyNode.ZIP_FILELIST_CACHE[str_zipped_path] = SimpleCache(
                        value=zip_file.namelist(),
                        expiration_date=datetime.utcnow() + timedelta(hours=2),
                    )
            return str_inside_zip_path in LazyNode.ZIP_FILELIST_CACHE[str_zipped_path].value
        else:
            return self.config.path.exists()

    def _get(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
        formatted: bool = True,
        get_node: bool = False,
    ) -> str | G | INode[G, S, V]:
        self._assert_url_end(url)

        if get_node:
            return self

        if expanded:
            if self.get_link_path().exists():
                return self.get_link_path().read_text()
            return self.get_lazy_content()

        return self.load(url, depth, expanded, formatted)

    @override
    def get(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
        formatted: bool = True,
    ) -> str | G:
        output = self._get(url, depth, expanded, formatted, get_node=False)
        assert not isinstance(output, INode)
        return output

    @override
    def get_node(
        self,
        url: Optional[List[str]] = None,
    ) -> INode[G, S, V]:
        output = self._get(url, get_node=True)
        assert isinstance(output, INode)
        return output

    @override
    def delete(self, url: Optional[List[str]] = None) -> None:
        self._assert_url_end(url)
        if self.get_link_path().exists():
            self.get_link_path().unlink()
        elif self.config.path.exists():
            self.config.path.unlink()

    def get_link_path(self) -> Path:
        path = self.config.path.parent / (self.config.path.name + ".link")
        return path

    @override
    def save(self, data: str | bytes | S, url: Optional[List[str]] = None) -> None:
        self._assert_not_in_zipped_file()
        self._assert_url_end(url)

        if isinstance(data, str) and self.matrix_mapper.matrix_exists(data):
            if isinstance(self.matrix_mapper, MatrixUriMapperManaged):
                self.get_link_path().write_text(data)
                if self.config.path.exists():
                    self.config.path.unlink()
            else:
                matrix = self.matrix_mapper.get_matrix(data)
                self.dump(cast(S, matrix))
            return None

        self.dump(cast(S, data), url)
        if self.get_link_path().exists():
            self.get_link_path().unlink()
        return None

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
