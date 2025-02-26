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
import contextlib
import io
import logging
from abc import ABC, abstractmethod
from enum import StrEnum
from pathlib import Path
from typing import List, Optional, Union, cast

import numpy as np
import pandas as pd
from numpy import typing as npt
from typing_extensions import override

from antarest.core.model import JSON
from antarest.core.utils.utils import StopWatch
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.exceptions import DenormalizationException
from antarest.study.storage.rawstudy.model.filesystem.lazy_node import LazyNode

logger = logging.getLogger(__name__)


class MatrixFrequency(StrEnum):
    """
    An enumeration of matrix frequencies.

    Each frequency corresponds to a specific time interval for a matrix's data.
    """

    ANNUAL = "annual"
    MONTHLY = "monthly"
    WEEKLY = "weekly"
    DAILY = "daily"
    HOURLY = "hourly"


def dump_dataframe(df: pd.DataFrame, path_or_buf: Path | io.BytesIO, float_format: Optional[str] = "%.6f") -> None:
    if df.empty and isinstance(path_or_buf, Path):
        path_or_buf.write_bytes(b"")
    else:
        df.to_csv(
            path_or_buf,
            sep="\t",
            header=False,
            index=False,
            float_format=float_format,
        )


def imports_matrix_from_bytes(data: bytes) -> Optional[npt.NDArray[np.float64]]:
    """Tries to convert bytes to a numpy array when importing a matrix"""
    str_data = data.decode("utf-8")
    if not str_data:
        return np.zeros(shape=(0, 0))
    for delimiter in [",", ";", "\t"]:
        with contextlib.suppress(Exception):
            df = pd.read_csv(io.BytesIO(data), delimiter=delimiter, header=None).replace(",", ".", regex=True)
            df = df.dropna(axis=1, how="all")  # We want to remove columns full of NaN at the import
            matrix = df.to_numpy(dtype=np.float64)
            return matrix
    return None


class MatrixNode(LazyNode[Union[bytes, JSON], Union[bytes, JSON], JSON], ABC):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        freq: MatrixFrequency,
    ) -> None:
        LazyNode.__init__(self, context, config)
        self.freq = freq

    @override
    def get_lazy_content(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
    ) -> str:
        return f"matrixfile://{self.config.path.name}"

    @override
    def normalize(self) -> None:
        # noinspection SpellCheckingInspection
        """
        Normalize the matrix by creating a link to the normalized version.
        The original matrix is then deleted.

        Skips the normalization process if the link path already exists
        or the matrix is zipped.

        Raises:
            DenormalizationException: if the original matrix retrieval fails.
        """
        if self.get_link_path().exists() or self.config.archive_path:
            return

        matrix = self.parse_as_dataframe()
        data = matrix.to_numpy().tolist()
        uuid = self.context.matrix.create(data)
        self.get_link_path().write_text(self.context.resolver.build_matrix_uri(uuid))
        self.config.path.unlink()

    @override
    def denormalize(self) -> None:
        """
        Read the matrix ID from the matrix link, retrieve the original matrix
        and write the matrix data to the file specified by `self.config.path`
        before removing the link file.
        """
        if self.config.path.exists() or not self.get_link_path().exists():
            return

        # noinspection SpellCheckingInspection
        logger.info(f"Denormalizing matrix {self.config.path}")
        uuid = self.get_link_path().read_text()
        matrix = self.context.resolver.resolve(uuid)
        if not matrix or not isinstance(matrix, dict):
            raise DenormalizationException(f"Failed to retrieve original matrix for {self.config.path}")

        self.dump(matrix)
        self.get_link_path().unlink()

    @override
    def load(
        self,
        url: Optional[List[str]] = None,
        depth: int = -1,
        expanded: bool = False,
        formatted: bool = True,
    ) -> Union[bytes, JSON]:
        file_path, _ = self._get_real_file_path()

        df = self.parse_as_dataframe(file_path)

        if formatted:
            stopwatch = StopWatch()
            data = cast(JSON, df.to_dict(orient="split"))
            stopwatch.log_elapsed(lambda x: logger.info(f"Matrix to dict in {x}s"))
            return data

        if df.empty:
            return b""
        buffer = io.BytesIO()
        np.savetxt(buffer, df, delimiter="\t", fmt="%.6f")
        return buffer.getvalue()

    @abstractmethod
    def parse_as_dataframe(self, file_path: Optional[Path] = None) -> pd.DataFrame:
        """
        Parse the matrix content and return it as a DataFrame object
        """
        raise NotImplementedError()

    @override
    def dump(
        self,
        data: Union[bytes, JSON],
        url: Optional[List[str]] = None,
    ) -> None:
        """
        Write matrix data to file.

        If the input data is of type bytes, write the data to file as is.
        Otherwise, convert the data to a Pandas DataFrame and write it to file as a tab-separated CSV.
        If the resulting DataFrame is empty, write an empty bytes object to file.

        Args:
            data: The data to write to file. If data is bytes, it will be written directly to file,
                otherwise it will be converted to a Pandas DataFrame and then written to file.
            url: node URL (not used here).
        """
        self.config.path.parent.mkdir(exist_ok=True, parents=True)
        if isinstance(data, bytes):
            self.config.path.write_bytes(data)
        else:
            df = pd.DataFrame(**data)
            dump_dataframe(df, self.config.path)
