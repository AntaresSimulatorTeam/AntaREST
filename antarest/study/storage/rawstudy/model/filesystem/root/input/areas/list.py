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


from typing_extensions import override

from antarest.core.utils.archives import extract_lines_from_archive
from antarest.matrixstore.matrix_uri_mapper import MatrixUriMapper
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.inode import INode

AREAS_LIST_RELATIVE_PATH = "input/areas/list.txt"


class InputAreasList(INode[list[str], list[str], list[str]]):
    def __init__(self, matrix_mapper: MatrixUriMapper, config: FileStudyTreeConfig):
        super().__init__(config)
        self.matrix_mapper = matrix_mapper

    @override
    def get_node_and_remainder(
        self,
        url: list[str] | None = None,
        depth: int = -1,
        expanded: bool = False,
        formatted: bool = True,
    ) -> tuple[INode[list[str], list[str], list[str]], list[str]]:
        return self, []

    @override
    def get(
        self,
        url: list[str] | None = None,
        depth: int = -1,
        expanded: bool = False,
        formatted: bool = True,
    ) -> list[str]:
        if self.config.archive_path:
            lines = extract_lines_from_archive(self.config.archive_path, AREAS_LIST_RELATIVE_PATH)
        else:
            lines = self.config.path.read_text().split("\n")
        return [line.strip() for line in lines if line.strip()]

    @override
    def save(self, data: list[str], url: list[str] | None = None) -> None:
        self._assert_not_in_zipped_file()
        self.config.path.write_text("\n".join(data))

    @override
    def delete(self, url: list[str] | None = None) -> None:
        if self.config.path.exists():
            self.config.path.unlink()
