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
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Generic, TypeAlias, TypeVar

from antarest.core.exceptions import WritingInsideZippedFileException
from antarest.core.utils.archives import read_original_file_in_archive
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig

if TYPE_CHECKING:
    from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixNode

G = TypeVar("G")
S = TypeVar("S")
V = TypeVar("V")


@dataclass
class OriginalFile:
    suffix: str
    content: bytes
    filename: str


class INode(ABC, Generic[G, S, V]):
    """
    Abstract tree element, have to be implemented to create hub or left.
    """

    def __init__(self, config: FileStudyTreeConfig):
        self.config = config

    @abstractmethod
    def get(
        self,
        url: list[str] | None = None,
        depth: int = -1,
        expanded: bool = False,
        formatted: bool = True,
    ) -> G:
        """
        Ask data inside tree.

        Args:
            url: data path to retrieve
            depth: after url is reached, node expand tree until matches depth asked
            expanded: context parameter to determine if current node become from a expansion
            formatted: ask for raw file transformation (for matrix)

        Returns: json

        """
        raise NotImplementedError()

    def get_node(
        self,
        url: list[str] | None = None,
    ) -> "INode[G,S,V]":
        """
        Returns the node object corresponding to the provided URL.
        """
        node, _ = self.get_node_and_remainder(url)
        return node

    @abstractmethod
    def get_node_and_remainder(
        self,
        url: list[str] | None = None,
    ) -> tuple["INode[G,S,V]", list[str]]:
        """
        Returns the node object corresponding to the provided URL,
        together with possibly unconsumed parts of the URL:
        nodes generally correspond to a folder or file, while URLs may point at
        data inside those nodes.
        """
        raise NotImplementedError()

    @abstractmethod
    def delete(self, url: list[str] | None = None) -> None:
        """
        Delete a node located at some url

        Args:
            url: data path to delete
        """

    @abstractmethod
    def save(self, data: S, url: list[str] | None = None) -> None:
        """
        Save data inside tree.

        Args:
            data: new data to save
            url: data path to change

        Returns:

        """
        raise NotImplementedError()

    def get_matrix_nodes_to_normalize(self) -> list["MatrixNode"]:
        """
        Scan tree to return matrix nodes to store in matrix store and replace by its links
        """
        return []

    def get_matrix_nodes_to_denormalize(self) -> list["MatrixNode"]:
        """
        Scan tree to return matrix nodes to replace its links by its data from the matrix store.
        """
        return []

    def get_file_content(self) -> OriginalFile:
        suffix = self.config.path.suffix
        filename = self.config.path.name
        if self.config.archive_path:
            content = read_original_file_in_archive(
                self.config.archive_path,
                self.get_relative_path_inside_archive(self.config.archive_path),
            )
            return OriginalFile(suffix=suffix, filename=filename, content=content)
        else:
            return OriginalFile(content=self.config.path.read_bytes(), suffix=suffix, filename=filename)

    def get_relative_path_inside_archive(self, archive_path: Path) -> str:
        return self.config.path.relative_to(archive_path.parent / self.config.study_id).as_posix()

    def _assert_url_end(self, url: list[str] | None = None) -> None:
        """
        Raise error if elements remain in url
        Args:
            url: data path

        Returns:

        """
        url = url or []
        if len(url) > 0:
            raise ValueError(f"url should be fully resolved when arrives on {self.__class__.__name__}")

    def _assert_not_in_zipped_file(self) -> None:
        """Prevents writing inside a zip file"""
        if self.config.archive_path:
            raise WritingInsideZippedFileException("Trying to save inside a zipped file")


TREE: TypeAlias = dict[str, INode[Any, Any, Any]]
