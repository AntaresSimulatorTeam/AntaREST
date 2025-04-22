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

from typing import List, Optional

from typing_extensions import override

from antarest.core.utils.archives import extract_lines_from_archive
from antarest.matrixstore.uri_resolver_service import MatrixUriMapper
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.inode import INode

AREAS_LIST_RELATIVE_PATH = "input/areas/list.txt"


class InputAreasList(INode[List[str], List[str], List[str]]):
    @override
    def normalize(self) -> None:
        pass  # no external store in this node

    @override
    def denormalize(self) -> None:
        pass  # no external store in this node

    def __init__(self, context: MatrixUriMapper, config: FileStudyTreeConfig):
        super().__init__(config)
        self.context = context

    @override
    def get_node(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
        formatted: bool = True,
    ) -> INode[List[str], List[str], List[str]]:
        return self

    @override
    def get(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
        formatted: bool = True,
    ) -> List[str]:
        if self.config.archive_path:
            lines = extract_lines_from_archive(self.config.archive_path, AREAS_LIST_RELATIVE_PATH)
        else:
            lines = self.config.path.read_text().split("\n")
        return [line.strip() for line in lines if line.strip()]

    @override
    def save(self, data: List[str], url: Optional[List[str]] = None) -> None:
        self._assert_not_in_zipped_file()
        self.config.path.write_text("\n".join(data))

    @override
    def delete(self, url: Optional[List[str]] = None) -> None:
        if self.config.path.exists():
            self.config.path.unlink()

    @override
    def check_errors(
        self,
        data: List[str],
        url: Optional[List[str]] = None,
        raising: bool = False,
    ) -> List[str]:
        errors = []
        if any(a not in data for a in [area.name for area in self.config.areas.values()]):
            errors.append(f"list.txt should have {self.config.area_names()} nodes but given {data}")
        return errors
