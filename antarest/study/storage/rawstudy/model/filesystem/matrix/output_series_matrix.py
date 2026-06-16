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

from antarest.core.exceptions import MustNotModifyOutputException
from antarest.core.model import JSON
from antarest.output.filestudy.utils import (
    load_output_file,
)
from antarest.study.model import MatrixFrequency
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.lazy_node import LazyNode

logger = logging.getLogger(__name__)


class OutputSeriesMatrix(LazyNode[bytes | JSON, bytes | JSON, JSON]):
    """
    Generic node to handle output matrix behavior.
    Node needs a DateSerializer and a HeadWriter to work
    """

    def __init__(self, config: FileStudyTreeConfig, freq: MatrixFrequency):
        super().__init__(config=config)
        self.freq = freq

    @override
    def get_lazy_content(self, url: list[str] | None = None, depth: int = -1, expanded: bool = False) -> str:
        return f"matrix://{self.config.path.name}"

    @override
    def load(
        self, url: list[str] | None = None, depth: int = -1, expanded: bool = False, formatted: bool = True
    ) -> bytes | JSON:
        return load_output_file(formatted, self.freq, self.config.path, self.config.study_id)

    @override
    def dump(self, data: bytes | JSON, url: list[str] | None = None) -> None:
        raise MustNotModifyOutputException(self.config.path.name)


class LinkOutputSeriesMatrix(OutputSeriesMatrix):
    def __init__(self, config: FileStudyTreeConfig, freq: MatrixFrequency, src: str, dest: str):
        super().__init__(config=config, freq=freq)


class AreaOutputSeriesMatrix(OutputSeriesMatrix):
    def __init__(self, config: FileStudyTreeConfig, freq: MatrixFrequency, area: str):
        super().__init__(config=config, freq=freq)


class BindingConstraintOutputSeriesMatrix(OutputSeriesMatrix):
    def __init__(self, config: FileStudyTreeConfig, freq: MatrixFrequency):
        super().__init__(config=config, freq=freq)
