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
from typing import List, Optional

import pandas as pd
from typing_extensions import override

from antarest.core.exceptions import ChildNotFoundError, MustNotModifyOutputException
from antarest.core.model import JSON
from antarest.study.model import MatrixFrequency
from antarest.study.output.utils import get_start_column, parse_output_file
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.lazy_node import LazyNode
from antarest.study.storage.rawstudy.model.filesystem.matrix.date_serializer import (
    FactoryDateSerializer,
    IDateMatrixSerializer,
)
from antarest.study.storage.rawstudy.model.filesystem.matrix.head_writer import (
    AreaHeadWriter,
    HeadWriter,
    LinkHeadWriter,
)

logger = logging.getLogger(__name__)


class OutputSeriesMatrix(LazyNode[bytes | JSON, bytes | JSON, JSON]):
    """
    Generic node to handle output matrix behavior.
    Node needs a DateSerializer and a HeadWriter to work
    """

    def __init__(
        self,
        config: FileStudyTreeConfig,
        freq: MatrixFrequency,
        date_serializer: IDateMatrixSerializer,
        head_writer: HeadWriter,
    ):
        super().__init__(config=config)
        self.date_serializer = date_serializer
        self.head_writer = head_writer
        self.freq = freq

    @override
    def get_lazy_content(self, url: Optional[List[str]] = None, depth: int = -1, expanded: bool = False) -> str:
        # noinspection SpellCheckingInspection
        return f"matrixfile://{self.config.path.name}"

    def parse_dataframe(self) -> pd.DataFrame:
        output_first_column = get_start_column(self.freq)
        file_path = self.config.path
        try:
            return parse_output_file(file_path, output_first_column).data
        except FileNotFoundError as e:
            # Raise 404 'Not Found' if the TSV file is not found
            logger.warning(f"Matrix file'{file_path}' not found")
            study_id = self.config.study_id
            relpath = file_path.relative_to(self.config.study_path).as_posix()
            raise ChildNotFoundError(f"File '{relpath}' not found in the study '{study_id}'") from e

    @override
    def load(
        self, url: list[str] | None = None, depth: int = -1, expanded: bool = False, formatted: bool = True
    ) -> bytes | JSON:
        if not formatted:
            try:
                return self.config.path.read_bytes()
            except FileNotFoundError:
                logger.warning(f"Missing file {self.config.path}")
                return b""

        matrix = self.parse_dataframe()
        return matrix.to_dict(orient="split", index=False)

    @override
    def dump(self, data: bytes | JSON, url: Optional[List[str]] = None) -> None:
        raise MustNotModifyOutputException(self.config.path.name)


class LinkOutputSeriesMatrix(OutputSeriesMatrix):
    def __init__(self, config: FileStudyTreeConfig, freq: MatrixFrequency, src: str, dest: str):
        super(LinkOutputSeriesMatrix, self).__init__(
            config=config,
            freq=freq,
            date_serializer=FactoryDateSerializer.create(freq, src),
            head_writer=LinkHeadWriter(src, dest, freq),
        )


class AreaOutputSeriesMatrix(OutputSeriesMatrix):
    def __init__(self, config: FileStudyTreeConfig, freq: MatrixFrequency, area: str):
        super(AreaOutputSeriesMatrix, self).__init__(
            config=config,
            freq=freq,
            date_serializer=FactoryDateSerializer.create(freq, area),
            head_writer=AreaHeadWriter(area, config.path.name[:2], freq),
        )


class BindingConstraintOutputSeriesMatrix(OutputSeriesMatrix):
    def __init__(self, config: FileStudyTreeConfig, freq: MatrixFrequency):
        super(BindingConstraintOutputSeriesMatrix, self).__init__(
            config=config,
            freq=freq,
            date_serializer=FactoryDateSerializer.create(freq, "system"),
            head_writer=AreaHeadWriter("system", config.path.name[:2], freq),
        )
