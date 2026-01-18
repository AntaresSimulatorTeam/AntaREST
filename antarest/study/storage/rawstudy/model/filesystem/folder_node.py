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

import shutil
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from typing_extensions import override

from antarest.core.exceptions import ChildNotFoundError, PathIsAFolderError
from antarest.core.model import JSON, SUB_JSON
from antarest.matrixstore.matrix_uri_mapper import MatrixUriMapper
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE, INode, OriginalFile
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixNode


class FilterError(Exception):
    pass


class FolderNode(INode[JSON, SUB_JSON, JSON], ABC):
    # noinspection SpellCheckingInspection
    """
    A node in the Antares tree structure that represents a folder in a filesystem.

    This class is responsible for forwarding requests deeper in the tree according
    to the provided URL, or expanding requests according to the depth of the folder
    structure. It is a hub node that can have child nodes added to it as required
    to build out the tree.

    The Antares tree structure is implemented in the
    `antarest.study.storage.rawstudy.model.filesystem` module.
    """

    def __init__(
        self,
        matrix_mapper: MatrixUriMapper,
        config: FileStudyTreeConfig,
        children_glob_exceptions: Optional[List[str]] = None,
    ) -> None:
        super().__init__(config)
        self.matrix_mapper = matrix_mapper
        self.children_glob_exceptions = children_glob_exceptions or []

    @abstractmethod
    def build(self) -> TREE:
        pass

    def _forward_get(
        self,
        url: List[str],
        depth: int,
        formatted: bool,
    ) -> JSON:
        children = self.build()
        names, sub_url = self._extract_child(children, url)
        # item is unique in url
        if len(names) == 1:
            child = children[names[0]]
            return child.get(sub_url, depth=depth, expanded=False, formatted=formatted)  # type: ignore
        # many items asked or * asked
        else:
            return {
                key: children[key].get(
                    sub_url,
                    depth=depth,
                    expanded=False,
                    formatted=formatted,
                )
                for key in names
            }

    def _expand_get(self, depth: int, formatted: bool) -> JSON:
        children = self.build()

        if depth == 0:
            return {}

        result: JSON = {}
        for name, node in children.items():
            # Hide optional matrices when neither .txt nor .link exists
            if isinstance(node, MatrixNode):
                should_exist = getattr(node, "should_exist", True)
                if not should_exist:
                    has_file = node.file_exists()
                    has_link = node.matrix_mapper.has_link(node)
                    if not has_file and not has_link:
                        continue

            result[name] = node.get(depth=depth - 1, expanded=True, formatted=formatted) if depth != 1 else {}

        return result

    @override
    def get(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
        formatted: bool = True,
    ) -> JSON:
        if url and url != [""]:
            return self._forward_get(url, depth, formatted)
        else:
            return self._expand_get(depth, formatted)

    @override
    def get_node_and_remainder(
        self,
        url: Optional[List[str]] = None,
    ) -> tuple[INode[JSON, SUB_JSON, JSON], list[str]]:
        if not url:
            return self, []
        children = self.build()
        names, sub_url = self._extract_child(children, url)
        if len(names) != 1:
            raise ValueError("Multiple nodes requested")
        child = children[names[0]]
        return child.get_node_and_remainder(sub_url)

    @override
    def save(
        self,
        data: SUB_JSON,
        url: Optional[List[str]] = None,
    ) -> None:
        self._assert_not_in_zipped_file()
        children = self.build()
        if not self.config.path.exists():
            self.config.path.mkdir()

        if url := url or []:
            (name,), sub_url = self._extract_child(children, url)
            return children[name].save(data, sub_url)
        else:
            assert isinstance(data, dict)
            for key in data:
                children[key].save(data[key])

    @override
    def delete(self, url: Optional[List[str]] = None) -> None:
        if url and url != [""]:
            children = self.build()
            names, sub_url = self._extract_child(children, url)
            for key in names:
                children[key].delete(sub_url)
        elif self.config.path.exists():
            shutil.rmtree(self.config.path)

    @override
    def get_matrix_nodes_to_normalize(self) -> list[MatrixNode]:
        nodes: list[MatrixNode] = []
        for child in self.build().values():
            node = child.get_matrix_nodes_to_normalize()
            nodes.extend(node)
        return nodes

    @override
    def get_matrix_nodes_to_denormalize(self) -> list[MatrixNode]:
        nodes: list[MatrixNode] = []
        for child in self.build().values():
            node = child.get_matrix_nodes_to_denormalize()
            nodes.extend(node)
        return nodes

    def _extract_child(self, children: TREE, url: List[str]) -> Tuple[List[str], List[str]]:
        names, sub_url = url[0].split(","), url[1:]
        names = (
            list(
                filter(
                    lambda c: c not in self.children_glob_exceptions,
                    children.keys(),
                )
            )
            if names[0] == "*"
            else names
        )

        if len(names) == 0:
            return [], sub_url

        if names[0] not in children:
            raise ChildNotFoundError(f"'{names[0]}' not a child of {self.__class__.__name__}")
        child_class = type(children[names[0]])
        for name in names:
            if name not in children:
                raise ChildNotFoundError(f"'{name}' not a child of {self.__class__.__name__}")
            if not isinstance(children[name], child_class):
                raise FilterError("Filter selection has different classes")
        return names, sub_url

    @override
    def get_file_content(self) -> OriginalFile:
        relative_path = self.config.path.relative_to(self.config.study_path).as_posix()
        raise PathIsAFolderError(f"Node at {relative_path} is a folder node.")
