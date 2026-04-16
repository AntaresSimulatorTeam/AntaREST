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

import numpy as np
import pandas as pd
from typing_extensions import override

from antarest.core.exceptions import ChildNotFoundError, MustNotModifyOutputException
from antarest.core.model import JSON
from antarest.matrixstore.matrix_uri_mapper import add_matrix_id_prefix
from antarest.output.filestudy.utils import get_start_column, parse_output_file
from antarest.output.model import VarColumn
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
        # noinspection SpellCheckingInspection
        return add_matrix_id_prefix(self.config.path.name)

    def parse_dataframe(self) -> pd.DataFrame:
        output_first_column = get_start_column(self.freq)
        file_path = self.config.path
        try:
            output = parse_output_file(file_path, output_first_column)
            df = output.data.to_pandas().astype(np.float64)
            df.columns = pd.MultiIndex.from_tuples(map(VarColumn.to_tuple, output.columns))
            return df
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
