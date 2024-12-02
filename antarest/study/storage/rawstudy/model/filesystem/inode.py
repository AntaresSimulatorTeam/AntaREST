# Copyright (c) 2024, RTE (https://www.rte-france.com)
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
from typing import Any, Dict, Generic, List, Optional, Tuple, TypeVar

from antarest.core.exceptions import ShouldNotHappenException, StudyNotArchived, WritingInsideZippedFileException
from antarest.core.utils.archives import extract_file_to_tmp_dir
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig

G = TypeVar("G")
S = TypeVar("S")
V = TypeVar("V")


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

    @abstractmethod
    def normalize(self) -> None:
        """
        Scan tree to send matrix in matrix store and replace by its links
        Returns:

        """
        raise NotImplementedError()

    @abstractmethod
    def denormalize(self) -> None:
        """
        Scan tree to fetch matrix by its links
        Returns:

        """
        raise NotImplementedError()

    def get_relative_path_inside_archive(self) -> Path:
        archive_path = self.config.archive_path
        if archive_path:
            return self.config.path.relative_to(archive_path.parent / self.config.study_id)
        else:
            raise StudyNotArchived(
                f"Study with uuid={self.config.study_id} supposed to be archived but archive_path is None."
            )

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


TREE = Dict[str, INode[Any, Any, Any]]
