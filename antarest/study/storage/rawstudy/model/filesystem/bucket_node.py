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

from collections.abc import Callable
from typing import Any

from typing_extensions import override

from antarest.core.model import SUB_JSON
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE, INode
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix_storage_context import MatrixStorageContext
from antarest.study.storage.rawstudy.model.filesystem.raw_file_node import RawFileNode


class RegisteredFile:
    def __init__(
        self,
        key: str,
        node: Callable[[MatrixStorageContext, FileStudyTreeConfig], INode[Any, Any, Any]],
        filename: str = "",
    ):
        self.key = key
        self.node = node
        self.filename = filename or key


class BucketNode(FolderNode):
    """
    Node to handle structure free, user purpose folder. BucketNode accept any file or sub folder as children.
    """

    def __init__(
        self,
        matrix_storage_context: MatrixStorageContext,
        config: FileStudyTreeConfig,
        registered_files: list[RegisteredFile] | None = None,
        use_matrix_mapper: bool = False,
    ):
        super().__init__(matrix_storage_context, config)
        self.registered_files: list[RegisteredFile] = registered_files or []
        self.use_matrix_mapper = use_matrix_mapper

    def _get_registered_file_by_key(self, key: str) -> RegisteredFile | None:
        return next((rf for rf in self.registered_files if rf.key == key), None)

    def _get_registered_file_by_filename(self, filename: str) -> RegisteredFile | None:
        return next((rf for rf in self.registered_files if rf.filename == filename), None)

    @override
    def save(
        self,
        data: SUB_JSON,
        url: list[str] | None = None,
    ) -> None:
        self._assert_not_in_zipped_file()
        if not self.config.path.exists():
            self.config.path.mkdir()

        if not url:
            assert isinstance(data, dict)
            for key, value in data.items():
                self._save(value, key)
        else:
            key = url[0]
            if len(url) > 1:
                registered_file = self._get_registered_file_by_key(key)
                if registered_file:
                    registered_file.node(self.matrix_storage_context, self.config.next_file(key)).save(data, url[1:])
                else:
                    BucketNode(self.matrix_storage_context, self.config.next_file(key)).save(data, url[1:])
            else:
                self._save(data, key)

    def _save(self, data: SUB_JSON, key: str) -> None:
        registered_file = self._get_registered_file_by_key(key)
        if registered_file:
            node = registered_file.node(self.matrix_storage_context, self.config.next_file(registered_file.filename))
        elif isinstance(data, dict):
            node = BucketNode(self.matrix_storage_context, self.config.next_file(key))
        elif isinstance(data, (str, bytes)):
            if self.use_matrix_mapper:
                node = InputSeriesMatrix(self.matrix_storage_context, self.config.next_file(key))
            else:
                node = RawFileNode(self.config.next_file(key))
        else:
            raise TypeError(repr(type(data)))
        node.save(data)

    @override
    def build(self) -> TREE:
        if not self.config.path.is_dir():
            return {}

        children: TREE = {}
        for item in sorted(self.config.path.iterdir()):
            registered_file = self._get_registered_file_by_filename(item.name)
            if registered_file:
                node = registered_file.node
                children[registered_file.key] = node(self.matrix_storage_context, self.config.next_file(item.name))
            elif item.is_file():
                if self.use_matrix_mapper:
                    children[item.name] = InputSeriesMatrix(
                        self.matrix_storage_context, self.config.next_file(item.name)
                    )
                else:
                    children[item.name] = RawFileNode(self.config.next_file(item.name))
            else:
                children[item.name] = BucketNode(self.matrix_storage_context, self.config.next_file(item.name))

        return children
