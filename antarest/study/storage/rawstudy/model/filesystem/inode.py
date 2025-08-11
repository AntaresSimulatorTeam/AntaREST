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
from pathlib import Path
from typing import Any, Dict, Generic, List, Optional, Tuple, TypeAlias, TypeVar

from antarest.core.exceptions import WritingInsideZippedFileException
from antarest.core.utils.archives import extract_file_to_tmp_dir, read_original_file_in_archive
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig

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
        url: Optional[List[str]] = None,
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

    @abstractmethod
    def get_node(
        self,
        url: Optional[List[str]] = None,
    ) -> "INode[G,S,V]":
        """
        Ask data inside tree.

        Args:
            url: data path to retrieve

        Returns: json

        """
        raise NotImplementedError()

    @abstractmethod
    def delete(self, url: Optional[List[str]] = None) -> None:
        """
        Delete a node located at some url

        Args:
            url: data path to delete
        """

    @abstractmethod
    def save(self, data: S, url: Optional[List[str]] = None) -> None:
        """
        Save data inside tree.

        Args:
            data: new data to save
            url: data path to change

        Returns:

        """
        raise NotImplementedError()

    @abstractmethod
    def check_errors(self, data: V, url: Optional[List[str]] = None, raising: bool = False) -> List[str]:
        """
        List inconsistency error between data and study configuration.
        Args:
            data: data to compare
            url: data path to compare
            raising: raise error if inconsistency occurs

        Returns: list of errors belongs to this node or children

        """
        raise NotImplementedError()

    def normalize(self) -> None:
        """
        Scan tree to send matrix in matrix store and replace by its links
        Returns:

        """
        pass

    def denormalize(self) -> None:
        """
        Scan tree to fetch matrix by its links
        Returns:

        """
        pass

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

    def _assert_url_end(self, url: Optional[List[str]] = None) -> None:
        """
        Raise error if elements remain in url
        Args:
            url: data path

        Returns:

        """
        url = url or []
        if len(url) > 0:
            raise ValueError(f"url should be fully resolved when arrives on {self.__class__.__name__}")

    def _extract_file_to_tmp_dir(self, archived_path: Path) -> Tuple[Path, Any]:
        """
        Happens when the file is inside an archive (aka self.config.zip_file is set)
        Unzip the file into a temporary directory.

        Returns:
            The actual path of the extracted file
            the tmp_dir object which MUST be cleared after use of the file
        """
        inside_archive_path = self.config.path.relative_to(archived_path.with_suffix(""))
        return extract_file_to_tmp_dir(archived_path, inside_archive_path)

    def _assert_not_in_zipped_file(self) -> None:
        """Prevents writing inside a zip file"""
        if self.config.archive_path:
            raise WritingInsideZippedFileException("Trying to save inside a zipped file")


TREE: TypeAlias = Dict[str, INode[Any, Any, Any]]
