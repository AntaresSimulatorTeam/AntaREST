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

import logging
from typing import List, Optional

from typing_extensions import override

from antarest.matrixstore.matrix_uri_mapper import MatrixUriMapper
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.lazy_node import LazyNode

logger = logging.getLogger(__name__)


class RawFileNode(LazyNode[bytes, bytes, str]):
    """
    Basic left which handle text file as like with any parsing / serialization
    """

    def __init__(self, matrix_mapper: MatrixUriMapper, config: FileStudyTreeConfig):
        LazyNode.__init__(self, config=config, matrix_mapper=matrix_mapper)

    @override
    def get_lazy_content(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
    ) -> str:
        return f"file://{self.config.path.name}"

    @override
    def load(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
        formatted: bool = True,
    ) -> bytes:
        file_path, tmp_dir = self._get_real_file_path()

        if file_path.exists():
            bytes = file_path.read_bytes()
        else:
            logger.warning(f"Missing file {self.config.path}")
            bytes = b""

        if tmp_dir:
            tmp_dir.cleanup()

        return bytes

    @override
    def dump(self, data: bytes, url: Optional[List[str]] = None) -> None:
        self.config.path.parent.mkdir(exist_ok=True, parents=True)
        self.config.path.write_bytes(data)

    @override
    def check_errors(self, data: str, url: Optional[List[str]] = None, raising: bool = False) -> List[str]:
        if not self.config.path.exists():
            msg = f"{self.config.path} not exist"
            if raising:
                raise ValueError(msg)
            return [msg]
        return []
