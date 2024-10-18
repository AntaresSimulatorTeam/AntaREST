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

import typing as t

from antarest.study.storage.rawstudy.model.filesystem.config.files import extract_lines_from_archive
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.inode import INode

AREAS_LIST_RELATIVE_PATH = "input/areas/list.txt"


class InputAreasList(INode[t.List[str], t.List[str], t.List[str]]):
    def normalize(self) -> None:
        pass  # no external store in this node

    def denormalize(self) -> None:
        pass  # no external store in this node

    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        super().__init__(config)
        self.context = context

    def get_node(
        self,
        url: t.Optional[t.List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
        formatted: bool = True,
    ) -> INode[t.List[str], t.List[str], t.List[str]]:
        return self

    def get(
        self,
        url: t.Optional[t.List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
        formatted: bool = True,
    ) -> t.List[str]:
        if self.config.archive_path:
            lines = extract_lines_from_archive(self.config.archive_path, AREAS_LIST_RELATIVE_PATH)
        else:
            lines = self.config.path.read_text().split("\n")
        return [l.strip() for l in lines if l.strip()]

    def save(self, data: t.List[str], url: t.Optional[t.List[str]] = None) -> None:
        self._assert_not_in_zipped_file()
        self.config.path.write_text("\n".join(data))

    def delete(self, url: t.Optional[t.List[str]] = None) -> None:
        if self.config.path.exists():
            self.config.path.unlink()

    def check_errors(
        self,
        data: t.List[str],
        url: t.Optional[t.List[str]] = None,
        raising: bool = False,
    ) -> t.List[str]:
        errors = []
        if any(a not in data for a in [area.name for area in self.config.areas.values()]):
            errors.append(f"list.txt should have {self.config.area_names()} nodes but given {data}")
        return errors
