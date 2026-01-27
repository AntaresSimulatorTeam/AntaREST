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
from abc import ABC, abstractmethod
from typing import Generic, List, Optional

from typing_extensions import override

from antarest.study.storage.rawstudy.model.filesystem.inode import G, INode, S, V


class LazyNode(INode, ABC, Generic[G, S, V]):  # type: ignore
    """
    A "lazy" node does not return its full content but a summarized, short representation
    when in the context of a tree expansion (typically getting children of a folder node).
    """

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
