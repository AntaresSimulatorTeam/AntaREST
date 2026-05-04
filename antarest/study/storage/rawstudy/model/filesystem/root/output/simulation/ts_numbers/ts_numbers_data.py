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

import logging

from typing_extensions import override

from antarest.core.model import JSON
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.lazy_node import LazyNode
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix_storage_context import MatrixStorageContext

logger = logging.getLogger(__name__)


class TsNumbersVector(LazyNode[list[int], list[int], JSON]):
    def __init__(self, matrix_storage_context: MatrixStorageContext, config: FileStudyTreeConfig):
        super().__init__(config)

    @override
    def load(
        self, url: list[str] | None = None, depth: int = -1, expanded: bool = False, formatted: bool = True
    ) -> list[int]:
        file_path = self.config.path

        if file_path.exists():
            with open(file_path) as fh:
                data = fh.readlines()

            if len(data) >= 1:
                return [int(d) for d in data[1:]]

        logger.warning(f"Missing file {self.config.path}")
        return []

    @override
    def dump(self, data: str | bytes | list[int], url: list[str] | None = None) -> None:
        self.config.path.parent.mkdir(exist_ok=True, parents=True)
        with open(self.config.path, "w") as fh:
            fh.write(f"size:1x{len(data)}\n")
            for d in data:
                fh.write(f"{d}\n")
